package com.mobilemoney.gateway.ussd

import android.accessibilityservice.AccessibilityService
import android.accessibilityservice.AccessibilityServiceInfo
import android.view.accessibility.AccessibilityEvent
import android.util.Log

class USSDListenerService : AccessibilityService() {
    companion object {
        var instance: USSDListenerService? = null
            private set
    }

    override fun onServiceConnected() {
        super.onServiceConnected()
        instance = this
        Log.d("USSDListener", "Accessibility service connected")
        val info = AccessibilityServiceInfo().apply {
            eventTypes = AccessibilityEvent.TYPE_WINDOW_CONTENT_CHANGED or AccessibilityEvent.TYPE_WINDOW_STATE_CHANGED
            feedbackType = AccessibilityServiceInfo.FEEDBACK_GENERIC
            notificationTimeout = 100
        }
        serviceInfo = info
    }

    override fun onAccessibilityEvent(event: AccessibilityEvent?) {
        if (event == null) return
        val packageName = event.packageName?.toString() ?: return
        if (!isPhonePackage(packageName)) return

        val text = event.text?.joinToString("\n") ?: return
        Log.d("USSDListener", "USSD screen text: $text")

        GatewayServiceHolder.onUSSDResponse(text)
    }

    override fun onInterrupt() {
        Log.w("USSDListener", "Accessibility service interrupted")
    }

    override fun onDestroy() {
        super.onDestroy()
        instance = null
    }

    private fun isPhonePackage(packageName: String): Boolean {
        val phonePackages = listOf(
            "com.android.phone",
            "com.google.android.dialer",
            "com.samsung.android.incallui",
            "com.android.server.telecom",
            "com.android.systemui"
        )
        return phonePackages.any { packageName.equals(it, ignoreCase = true) }
    }
}
