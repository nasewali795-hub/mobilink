package com.mobilemoney.gateway.service

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.app.Service
import android.content.Intent
import android.os.Build
import android.os.IBinder
import android.util.Log
import androidx.core.app.NotificationCompat
import com.mobilemoney.gateway.R
import com.mobilemoney.gateway.ui.GatewayActivity

class GatewayService : Service() {
    private lateinit var webSocketClient: org.java_websocket.client.WebSocketClient
    private var currentTransaction: TransactionCommand? = null
    private var currentStepIndex = 0
    private var currentSteps: List<USSDStep> = emptyList()
    private var ussdSessionActive = false
    private var ussdRetryCount = 0
    private val maxRetries = 2
    private val ussdTimeoutMs = 120000L
    private val mainHandler = android.os.Handler(android.os.Looper.getMainLooper())
    private val consecutiveFailures = java.util.concurrent.atomic.AtomicInteger(0)
    private val maxConsecutiveFailures = 3
    private var currentSubcriptionId: Int = -1

    private val ussdTimeoutRunnable = Runnable {
        if (ussdSessionActive) {
            Log.w(TAG, "USSD timeout after $ussdTimeoutMs ms")
            failCurrentTransaction("USSD session timeout")
        }
    }

    override fun onCreate() {
        super.onCreate()
        Log.d(TAG, "Service created")
        GatewayServiceHolder.bind(this)
        startForegroundService()
        startWebSocketConnection()
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        when (intent?.action) {
            "ACTION_SMS_RECEIVED" -> {
                val sender = intent.getStringExtra("sms_sender")
                val message = intent.getStringExtra("sms_message")
                val status = intent.getStringExtra("parsed_status")
                val transactionId = intent.getStringExtra("parsed_transaction_id")
                val amount = intent.getDoubleExtra("parsed_amount", 0.0)
                val reference = intent.getStringExtra("parsed_reference")
                handleInboundSMS(sender, message, status, transactionId, amount, reference)
            }
            "ACTION_USSD_INPUT" -> {
                val input = intent.getStringExtra("ussd_input") ?: ""
                handleUSSDInput(input)
            }
        }
        return START_STICKY
    }

    override fun onBind(intent: Intent?): IBinder? = null

    private fun startForegroundService() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val channel = NotificationChannel(
                CHANNEL_ID,
                "Gateway Service",
                NotificationManager.IMPORTANCE_LOW
            ).apply {
                description = "Keeps the mobile money gateway active"
                setShowBadge(false)
            }
            val manager = getSystemService(NotificationManager::class.java)
            manager.createNotificationChannel(channel)
        }

        val notificationIntent = Intent(this, GatewayActivity::class.java)
        val pendingIntent = PendingIntent.getActivity(
            this, 0, notificationIntent,
            PendingIntent.FLAG_IMMUTABLE or PendingIntent.FLAG_UPDATE_CURRENT
        )

        val notification = NotificationCompat.Builder(this, CHANNEL_ID)
            .setContentTitle("Mobile Money Gateway")
            .setContentText("Gateway service is running")
            .setSmallIcon(android.R.drawable.ic_dialog_info)
            .setContentIntent(pendingIntent)
            .setOngoing(true)
            .build()

        startForeground(NOTIFICATION_ID, notification)
    }

    private fun startWebSocketConnection() {
        val serverUri = URI.create("wss://mobilink-app.onrender.com/gateway/ws/connect/gateway-1")
        webSocketClient = object : WebSocketClient(serverUri) {
            override fun onOpen(handshake: ServerHandshake?) {
                Log.d(TAG, "WebSocket connected")
                consecutiveFailures.set(0)
                send("{ \"type\": \"heartbeat\", \"status\": \"online\", \"timestamp\": ${System.currentTimeMillis()} }")
                reportSimStatus()
            }

            override fun onMessage(message: String?) {
                Log.d(TAG, "Message received: $message")
                message?.let { handleServerMessage(it) }
            }

            override fun onClose(code: Int, reason: String?, remote: Boolean) {
                Log.w(TAG, "WebSocket closed: $reason")
                reconnectWebSocket()
            }

            override fun onError(ex: Exception?) {
                Log.e(TAG, "WebSocket error", ex)
                consecutiveFailures.incrementAndGet()
            }
        }
        webSocketClient.connect()
    }

    private fun reconnectWebSocket() {
        Thread {
            val delay = (3000L * (1 shl consecutiveFailures.get())).coerceAtMost(30000L)
            Log.d(TAG, "Reconnecting in ${delay}ms")
            Thread.sleep(delay)
            if (!webSocketClient.isOpen) {
                startWebSocketConnection()
            }
        }.start()
    }

    private fun handleServerMessage(message: String) {
        try {
            val json = org.json.JSONObject(message)
            when (json.optString("type")) {
                "execute_ussd" -> {
                    val transactionId = json.optString("transaction_id")
                    val simSlot = json.optString("sim_slot")
                    val network = json.optString("network")
                    val operation = json.optString("operation")
                    val customerPhone = json.optString("customer_phone")
                    val amount = json.optDouble("amount")
                    val pin = json.optString("pin")

                    if (transactionId.isBlank() || simSlot.isBlank()) {
                        Log.e(TAG, "Invalid execute_ussd command: missing transaction_id or sim_slot")
                        return
                    }

                    currentTransaction = TransactionCommand(transactionId, simSlot, network, operation, customerPhone, amount, pin)
                    currentSteps = buildSteps(network, operation, simSlot, customerPhone, amount, pin)
                    currentStepIndex = 0
                    ussdRetryCount = 0
                    ussdSessionActive = true
                    currentSubcriptionId = getSubscriptionIdForSlot(simSlot)

                    mainHandler.postDelayed(ussdTimeoutRunnable, ussdTimeoutMs)
                    executeNextStep()
                }
                "cancel_transaction" -> {
                    Log.d(TAG, "Cancelling current transaction")
                    resetTransactionState()
                }
                "ping" -> {
                    send("{ \"type\": \"pong\", \"timestamp\": ${System.currentTimeMillis()} }")
                }
            }
        } catch (e: Exception) {
            Log.e(TAG, "Failed to parse server message", e)
        }
    }

    private fun buildSteps(network: String, operation: String, slotIndex: String, phone: String, amount: Double, pin: String?): List<USSDStep> {
        return when (network.lowercase()) {
            "mtn" -> USSDExecutor.buildMTN(operation, slotIndex, phone, amount, pin)
            "airtel" -> USSDExecutor.buildAirtel(operation, slotIndex, phone, amount, pin)
            "zamtel" -> USSDExecutor.buildZamtel(operation, slotIndex, phone, amount, pin)
            else -> {
                Log.w(TAG, "Unknown network: $network")
                emptyList()
            }
        }
    }

    fun executeNextStep() {
        if (!ussdSessionActive) return
        if (currentStepIndex >= currentSteps.size) {
            Log.d(TAG, "USSD steps completed")
            completeCurrentTransaction()
            return
        }

        val step = currentSteps[currentStepIndex]
        Log.d(TAG, "Executing step ${currentStepIndex + 1}/${currentSteps.size}: ${step.type}")

        when (step.type) {
            "ussd" -> {
                sendTransactionUpdate("executing_ussd", "Dialing ${step.value}")
                USSDService.dialUSSD(this@GatewayService, step.value.orEmpty(), step.simSlot.orEmpty())
            }
            "ussd_response" -> {
                Log.d(TAG, "Waiting for USSD response matching: ${step.expectedPattern}")
            }
            "ussd_input" -> {
                Log.d(TAG, "Sending input: ${step.value}")
                USSDService.sendInput(step.value.orEmpty())
            }
            else -> {
                Log.w(TAG, "Unknown step type: ${step.type}")
                executeNextStep()
            }
        }
    }

    fun onUSSDResponseReceived(text: String) {
        if (!ussdSessionActive || currentSteps.isEmpty()) return

        Log.d(TAG, "USSD screen text received: $text")

        val currentStep = currentSteps.getOrNull(currentStepIndex)
        if (currentStep == null) {
            Log.w(TAG, "No current step available")
            return
        }

        when (currentStep.type) {
            "ussd_response" -> {
                val matches = USSDExecutor.matchesPattern(text, currentStep.expectedPattern)
                Log.d(TAG, "Pattern '${currentStep.expectedPattern}' matches: $matches")
                if (matches) {
                    mainHandler.removeCallbacks(ussdTimeoutRunnable)
                    mainHandler.postDelayed(ussdTimeoutRunnable, ussdTimeoutMs)
                    currentStepIndex++
                    executeNextStep()
                }
            }
            "ussd" -> {
                if (text.contains("error", ignoreCase = true) || text.contains("unavailable", ignoreCase = true)) {
                    failCurrentTransaction("Network error: $text")
                }
            }
        }
    }

    fun onInputSent(input: String) {
        if (!ussdSessionActive) return
        mainHandler.removeCallbacks(ussdTimeoutRunnable)
        mainHandler.postDelayed(ussdTimeoutRunnable, ussdTimeoutMs)
        currentStepIndex++
        executeNextStep()
    }

    private fun handleInboundSMS(sender: String?, message: String?, status: String?, transactionId: String?, amount: Double?, reference: String?) {
        Log.d(TAG, "Inbound SMS handler: sender=$sender, status=$status, txn=$transactionId")
        if (transactionId != null && currentTransaction?.transactionId == transactionId) {
            when (status) {
                "success" -> completeCurrentTransaction(reference)
                "failed" -> failCurrentTransaction("SMS reported failure")
                "unrecognized" -> {
                    Log.w(TAG, "SMS could not be parsed, requiring manual review")
                    sendTransactionUpdate("requires_manual_review", "SMS parsing ambiguous")
                    resetTransactionState()
                }
            }
        }
    }

    private fun handleUSSDInput(input: String) {
        Log.d(TAG, "Received USSD input: $input")
    }

    private fun completeCurrentTransaction(reference: String? = null) {
        resetTransactionState()
        sendTransactionUpdate("success", reference ?: "Transaction completed")
        consecutiveFailures.set(0)
    }

    private fun failCurrentTransaction(reason: String) {
        Log.e(TAG, "Transaction failed: $reason")
        sendTransactionUpdate("failed", reason)
        resetTransactionState()
        consecutiveFailures.incrementAndGet()
    }

    private fun resetTransactionState() {
        ussdSessionActive = false
        mainHandler.removeCallbacks(ussdTimeoutRunnable)
        currentTransaction = null
        currentSteps = emptyList()
        currentStepIndex = 0
        ussdRetryCount = 0
        currentSubcriptionId = -1
    }

    fun sendTransactionUpdate(status: String, detail: String? = null) {
        val transactionId = currentTransaction?.transactionId
        val payload = org.json.JSONObject().apply {
            put("type", "transaction_update")
            put("transaction_id", transactionId)
            put("status", status)
            put("slot_index", currentTransaction?.simSlot)
            put("network", currentTransaction?.network)
            if (detail != null) put("detail", detail)
            put("timestamp", System.currentTimeMillis())
        }
        if (webSocketClient.isOpen) {
            webSocketClient.send(payload.toString())
        }
    }

    private fun reportSimStatus() {
        try {
            val sims = DualSimManager.getActiveSims(this)
            val payload = org.json.JSONObject().apply {
                put("type", "sim_status")
                put("timestamp", System.currentTimeMillis())
                val simArray = org.json.JSONArray()
                sims.forEach { sim ->
                    val obj = org.json.JSONObject().apply {
                        put("slot_index", sim.slotIndex)
                        put("subscription_id", sim.subscriptionId)
                        put("carrier_name", sim.carrierName)
                        put("phone_number", sim.phoneNumber)
                        put("is_active", sim.isActive)
                    }
                    simArray.put(obj)
                }
                put("sims", simArray)
                put("dual_sim", sims.size > 1)
            }
            if (webSocketClient.isOpen) {
                webSocketClient.send(payload.toString())
            }
        } catch (e: Exception) {
            Log.e(TAG, "Failed to report SIM status", e)
        }
    }

    private fun getSubscriptionIdForSlot(simSlot: String): Int {
        val slot = simSlot.toIntOrNull() ?: return -1
        return DualSimManager.getSimForSlot(this, simSlot)?.subscriptionId ?: -1
    }

    override fun onDestroy() {
        super.onDestroy()
        GatewayServiceHolder.unbind()
        mainHandler.removeCallbacks(ussdTimeoutRunnable)
        if (::webSocketClient.isInitialized && webSocketClient.isOpen) {
            webSocketClient.close()
        }
    }

    companion object {
        const val TAG = "GatewayService"
        const val CHANNEL_ID = "GatewayServiceChannel"
        const val NOTIFICATION_ID = 1001
    }
}
