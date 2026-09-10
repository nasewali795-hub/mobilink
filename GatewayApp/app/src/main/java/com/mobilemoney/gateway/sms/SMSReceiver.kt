package com.mobilemoney.gateway.sms

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.os.Bundle
import android.telephony.SmsMessage
import android.util.Log
import com.mobilemoney.gateway.util.SMSParser

class SMSReceiver : BroadcastReceiver() {
    override fun onReceive(context: Context?, intent: Intent?) {
        if (intent?.action != "android.provider.Telephony.SMS_RECEIVED") return

        val bundle = intent.extras ?: return
        val pdus = bundle.get("pdus") as? Array<*>
        if (pdus == null || pdus.isEmpty()) return

        val messages = pdus.mapNotNull { pdu ->
            val format = bundle.getString("format")
            try {
                SmsMessage.createFromPdu(pdu as ByteArray, format)
            } catch (e: Exception) {
                Log.w("SMSReceiver", "Failed to parse PDU", e)
                null
            }
        }

        val sender = messages.firstOrNull()?.originatingAddress
        val messageBody = messages.mapNotNull { it.messageBody }.joinToString("\n")

        if (sender == null || messageBody.isBlank()) return

        Log.d("SMSReceiver", "SMS from $sender: $messageBody")

        if (!SMSParser.isMnoNotification(messageBody)) return

        val parsed = SMSParser.parse(messageBody, sender)
        Log.d("SMSReceiver", "Parsed SMS: $parsed")

        val serviceIntent = Intent(context, com.mobilemoney.gateway.service.GatewayService::class.java).apply {
            action = "ACTION_SMS_RECEIVED"
            putExtra("sms_sender", sender)
            putExtra("sms_message", messageBody)
            putExtra("parsed_status", parsed.status)
            putExtra("parsed_transaction_id", parsed.transactionId)
            putExtra("parsed_amount", parsed.amount ?: 0.0)
            putExtra("parsed_reference", parsed.reference)
        }

        try {
            if (context != null) {
                if (android.os.Build.VERSION.SDK_INT >= android.os.Build.VERSION_CODES.O) {
                    context.startForegroundService(serviceIntent)
                } else {
                    context.startService(serviceIntent)
                }
            }
        } catch (e: Exception) {
            Log.e("SMSReceiver", "Failed to start service for SMS", e)
        }
    }
}
