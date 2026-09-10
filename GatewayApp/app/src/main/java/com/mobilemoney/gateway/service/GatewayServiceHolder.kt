package com.mobilemoney.gateway.service

import android.util.Log

object GatewayServiceHolder {
    private var gatewayService: GatewayService? = null
    private const val TAG = "GatewayServiceHolder"

    fun bind(service: GatewayService) {
        gatewayService = service
        Log.d(TAG, "GatewayService bound")
    }

    fun unbind() {
        gatewayService = null
        Log.d(TAG, "GatewayService unbound")
    }

    fun onUSSDResponse(text: String) {
        Log.d(TAG, "USSD response received: $text")
        gatewayService?.onUSSDResponseReceived(text)
    }

    fun onInputSent(input: String) {
        Log.d(TAG, "USSD input sent: $input")
        gatewayService?.onInputSent(input)
    }

    fun getStatus(): String {
        return if (gatewayService != null) "online" else "offline"
    }
}
