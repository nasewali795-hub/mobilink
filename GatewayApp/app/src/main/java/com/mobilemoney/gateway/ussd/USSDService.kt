package com.mobilemoney.gateway.ussd

import android.content.Context
import android.telephony.TelephonyManager
import android.util.Log
import java.lang.reflect.Method
import android.os.Build
import com.mobilemoney.gateway.service.GatewayServiceHolder

object USSDService {
    private const val TAG = "USSDService"

    fun dialUSSD(context: Context, ussdCode: String, simSlot: String) {
        Log.d(TAG, "Dialing USSD: $ussdCode on slot $simSlot")
        try {
            val telephonyManager = context.getSystemService(android.content.Context.TELEPHONY_SERVICE) as TelephonyManager
            val slotIndex = simSlot.toIntOrNull() ?: 0

            val subscriptionId = getSubscriptionIdForSlot(context, slotIndex)
            val subTelephonyManager = if (subscriptionId != -1 && Build.VERSION.SDK_INT >= Build.VERSION_CODES.LOLLIPOP_MR1) {
                telephonyManager.createForSubscriptionId(subscriptionId)
            } else {
                telephonyManager
            }

            val method = findSendUssdRequestMethod(subTelephonyManager) ?: findSendUssdRequestMethod(telephonyManager)
            if (method != null) {
                method.invoke(subTelephonyManager ?: telephonyManager, ussdCode, object : TelephonyManager.UssdResponseCallback() {
                    override fun onReceiveUssdResponse(telephonyManager: TelephonyManager, request: String, response: CharSequence) {
                        Log.d(TAG, "USSD response: $response")
                        GatewayServiceHolder.onUSSDResponse(response.toString())
                    }

                    override fun onReceiveUssdResponseFailed(telephonyManager: TelephonyManager, request: String, failureCode: Int) {
                        Log.e(TAG, "USSD failed with code: $failureCode")
                        GatewayServiceHolder.onUSSDResponse("[USSD_FAILED:$failureCode]")
                    }
                })
            } else {
                Log.e(TAG, "sendUssdRequest method not found on this device")
                GatewayServiceHolder.onUSSDResponse("[USSD_METHOD_NOT_FOUND]")
            }
        } catch (e: Exception) {
            Log.e(TAG, "Failed to dial USSD", e)
            GatewayServiceHolder.onUSSDResponse("[USSD_EXCEPTION:${e.message}]")
        }
    }

    fun sendInput(text: String) {
        Log.d(TAG, "Sending USSD input: $text")
        GatewayServiceHolder.onInputSent(text)
    }

    private fun getSubscriptionIdForSlot(context: Context, slotIndex: Int): Int {
        return try {
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.LOLLIPOP_MR1) {
                val subscriptionManager = context.getSystemService(android.content.Context.TELEPHONY_SUBSCRIPTION_SERVICE) as? android.telephony.SubscriptionManager
                val subscriptions = subscriptionManager?.activeSubscriptionInfoList
                val info = subscriptions?.find { it.simSlotIndex == slotIndex }
                info?.subscriptionId ?: -1
            } else {
                -1
            }
        } catch (e: Exception) {
            Log.w(TAG, "Cannot get subscription ID for slot $slotIndex", e)
            -1
        }
    }

    private fun findSendUssdRequestMethod(telephonyManager: TelephonyManager?): Method? {
        if (telephonyManager == null) return null
        return try {
            telephonyManager.javaClass.getDeclaredMethod(
                "sendUssdRequest",
                String::class.java,
                TelephonyManager.UssdResponseCallback::class.java
            )
        } catch (e: NoSuchMethodException) {
            Log.w(TAG, "sendUssdRequest(String, UssdResponseCallback) not found")
            null
        }
    }
}
