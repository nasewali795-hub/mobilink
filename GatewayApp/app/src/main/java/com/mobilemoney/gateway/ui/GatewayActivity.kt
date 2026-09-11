package com.mobilemoney.gateway.ui

import androidx.core.app.ActivityCompat
import android.Manifest
import android.content.pm.PackageManager

import android.accessibilityservice.AccessibilityServiceInfo
import android.content.Context
import android.content.Intent
import android.os.Bundle
import android.provider.Settings
import com.mobilemoney.gateway.service.GatewayServiceHolder
import android.util.Log
import android.view.View
import android.widget.Button
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity
import com.mobilemoney.gateway.R
import com.mobilemoney.gateway.service.GatewayService
import com.mobilemoney.gateway.ussd.USSDListenerService
import com.mobilemoney.gateway.util.DualSimManager

class GatewayActivity : AppCompatActivity() {
    private lateinit var statusText: TextView
    private lateinit var currentTransactionText: TextView
    private lateinit var simStatusText: TextView
    private lateinit var networkStatusText: TextView
    private lateinit var startServiceButton: Button
    private lateinit var stopServiceButton: Button
    private lateinit var openAccessibilityButton: Button
    private lateinit var refreshSimButton: Button

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        
        // Request essential runtime permissions to prevent crashes
        val permissions = mutableListOf(
            Manifest.permission.READ_PHONE_STATE,
            Manifest.permission.RECEIVE_SMS,
            Manifest.permission.READ_SMS,
            Manifest.permission.SEND_SMS,
            Manifest.permission.CALL_PHONE
        )
        if (android.os.Build.VERSION.SDK_INT >= android.os.Build.VERSION_CODES.TIRAMISU) {
            permissions.add(Manifest.permission.POST_NOTIFICATIONS)
        }
        
        val missingPermissions = permissions.filter { 
            ActivityCompat.checkSelfPermission(this, it) != PackageManager.PERMISSION_GRANTED 
        }
        
        if (missingPermissions.isNotEmpty()) {
            ActivityCompat.requestPermissions(this, missingPermissions.toTypedArray(), 100)
        }
        setContentView(R.layout.activity_gateway)

        statusText = findViewById(R.id.statusText)
        currentTransactionText = findViewById(R.id.currentTransactionText)
        simStatusText = findViewById(R.id.simStatusText)
        networkStatusText = findViewById(R.id.networkStatusText)
        startServiceButton = findViewById(R.id.startServiceButton)
        stopServiceButton = findViewById(R.id.stopServiceButton)
        openAccessibilityButton = findViewById(R.id.openAccessibilitySettings)
        refreshSimButton = findViewById(R.id.refreshSimButton)

        startServiceButton.setOnClickListener { startGatewayService() }
        stopServiceButton.setOnClickListener { stopGatewayService() }
        openAccessibilityButton.setOnClickListener { openAccessibilitySettings() }
        refreshSimButton.setOnClickListener { updateSimStatus() }

        updateUI()
        updateSimStatus()
    }

    override fun onResume() {
        super.onResume()
        updateUI()
        updateSimStatus()
    }

    private fun startGatewayService() {
        val serviceIntent = Intent(this, GatewayService::class.java)
        if (android.os.Build.VERSION.SDK_INT >= android.os.Build.VERSION_CODES.O) {
            startForegroundService(serviceIntent)
        } else {
            startService(serviceIntent)
        }
        updateUI()
    }

    private fun stopGatewayService() {
        val serviceIntent = Intent(this, GatewayService::class.java)
        stopService(serviceIntent)
        updateUI()
    }

    private fun openAccessibilitySettings() {
        val intent = Intent(Settings.ACTION_ACCESSIBILITY_SETTINGS)
        startActivity(intent)
    }

    private fun updateUI() {
        val isAccessibilityEnabled = isAccessibilityServiceEnabled(this, USSDListenerService::class.java)
        openAccessibilityButton.text = if (isAccessibilityEnabled) {
            "Accessibility Service: Enabled"
        } else {
            "Enable Accessibility Service"
        }

        val isServiceRunning = GatewayServiceHolder.getStatus() == "online"
        statusText.text = if (isServiceRunning) {
            "Gateway: Connected"
        } else {
            "Gateway: Disconnected"
        }
    }

    private fun updateSimStatus() {
        try {
            val sims = DualSimManager.getActiveSims(this)
            val simStatus = sims.joinToString(" | ") { sim ->
                "SIM${sim.slotIndex}: ${sim.carrierName ?: "Unknown"} (${sim.phoneNumber ?: "No number"})"
            }
            simStatusText.text = if (sims.isEmpty()) {
                "No SIM cards detected"
            } else {
                "SIMs: $simStatus"
            }

            val isDual = DualSimManager.isDualSim(this)
            networkStatusText.text = if (isDual) {
                "Dual SIM mode: Active"
            } else if (sims.size == 1) {
                "Single SIM mode"
            } else {
                "No SIM available"
            }
        } catch (e: Exception) {
            Log.e("GatewayActivity", "Failed to update SIM status", e)
            simStatusText.text = "SIM status unavailable"
            networkStatusText.text = "Permission required"
        }
    }

    private fun isAccessibilityServiceEnabled(context: Context, service: Class<out android.accessibilityservice.AccessibilityService>): Boolean {
        val enabledServices = Settings.Secure.getString(context.contentResolver, Settings.Secure.ENABLED_ACCESSIBILITY_SERVICES)
        val componentName = "${context.packageName}/${service.name}"
        return enabledServices?.contains(componentName) == true
    }
}
