package com.mobilemoney.gateway.ussd

import android.content.Context
import android.content.Intent
import android.net.Uri
import android.os.Build
import android.os.Handler
import android.os.Looper
import android.telephony.TelephonyManager
import android.util.Log
import com.mobilemoney.gateway.service.GatewayServiceHolder

object USSDService {
    private const val TAG = "USSDService"

    fun dialUSSD(context: Context, ussdCode: String, simSlot: String) {
        Log.d(TAG, "Dialing USSD: $ussdCode on slot $simSlot")

        val slotIndex = simSlot.toIntOrNull() ?: 0

        // Primary method: Use public TelephonyManager API (Android 8+, API 26+)
        // This correctly passes a Handler as the 3rd parameter (previously missing — that was the bug)
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            try {
                val telephonyManager = context.getSystemService(Context.TELEPHONY_SERVICE) as TelephonyManager
                val subscriptionId = getSubscriptionIdForSlot(context, slotIndex)
                val tm = if (subscriptionId != -1) {
                    telephonyManager.createForSubscriptionId(subscriptionId)
                } else {
                    telephonyManager
                }

                val mainHandler = Handler(Looper.getMainLooper())
                tm.sendUssdRequest(ussdCode, object : TelephonyManager.UssdResponseCallback() {
                    override fun onReceiveUssdResponse(
                        tm: TelephonyManager,
                        request: String,
                        response: CharSequence
                    ) {
                        Log.d(TAG, "USSD response received: $response")
                        GatewayServiceHolder.onUSSDResponse(response.toString())
                    }

                    override fun onReceiveUssdResponseFailed(
                        tm: TelephonyManager,
                        request: String,
                        failureCode: Int
                    ) {
                        Log.e(TAG, "USSD failed with code: $failureCode")
                        // Fallback to Intent dial on failure
                        dialViaIntent(context, ussdCode)
                        GatewayServiceHolder.onUSSDResponse("[USSD_FAILED:$failureCode]")
                    }
                }, mainHandler)

                Log.d(TAG, "USSD request sent via TelephonyManager API")
                return
            } catch (e: Exception) {
                Log.w(TAG, "TelephonyManager API failed, falling back to Intent: ${e.message}")
            }
        }

        // Fallback: Dial via Intent (shows USSD dialog on screen — works on all Android versions)
        // AccessibilityService will capture the response from the screen
        dialViaIntent(context, ussdCode)
    }

    /**
     * Dials USSD by launching the phone dialer via Intent.
     * This is the most reliable method — it physically opens the dialer
     * and shows the USSD dialog on screen. The USSDListenerService
     * (AccessibilityService) then captures the response text.
     */
    private fun dialViaIntent(context: Context, ussdCode: String) {
        try {
            Log.d(TAG, "Dialing via Intent: $ussdCode")
            val encodedCode = Uri.encode(ussdCode)
            val intent = Intent(Intent.ACTION_CALL, Uri.parse("tel:$encodedCode")).apply {
                flags = Intent.FLAG_ACTIVITY_NEW_TASK
            }
            context.startActivity(intent)
            Log.d(TAG, "Intent dial launched for: $ussdCode")
        } catch (e: Exception) {
            Log.e(TAG, "Intent dial also failed: ${e.message}", e)
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
                val subscriptionManager = context.getSystemService(
                    Context.TELEPHONY_SUBSCRIPTION_SERVICE
                ) as? android.telephony.SubscriptionManager
                val info = subscriptionManager?.activeSubscriptionInfoList
                    ?.find { it.simSlotIndex == slotIndex }
                info?.subscriptionId ?: -1
            } else {
                -1
            }
        } catch (e: Exception) {
            Log.w(TAG, "Cannot get subscription ID for slot $slotIndex", e)
            -1
        }
    }
}
