package com.mobilemoney.gateway.util

import android.content.Context
import android.os.Build
import android.telephony.SubscriptionInfo
import android.telephony.SubscriptionManager
import android.telephony.TelephonyManager
import android.util.Log

object DualSimManager {
    private const val TAG = "DualSimManager"

    data class SimInfo(
        val slotIndex: Int,
        val subscriptionId: Int,
        val carrierName: String?,
        val phoneNumber: String?,
        val isoCountryCode: String?,
        val isActive: Boolean
    )

    fun getActiveSims(context: Context): List<SimInfo> {
        val sims = mutableListOf<SimInfo>()
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.LOLLIPOP_MR1) {
            val subscriptionManager = context.getSystemService(android.content.Context.TELEPHONY_SUBSCRIPTION_SERVICE) as? SubscriptionManager
            if (subscriptionManager != null) {
                try {
                    val subscriptions = subscriptionManager.activeSubscriptionInfoList
                    subscriptions?.forEach { info ->
                        sims.add(
                            SimInfo(
                                slotIndex = info.simSlotIndex,
                                subscriptionId = info.subscriptionId,
                                carrierName = info.carrierName?.toString(),
                                phoneNumber = info.number,
                                isoCountryCode = info.countryIso,
                                isActive = true
                            )
                        )
                    }
                } catch (e: SecurityException) {
                    Log.e(TAG, "Missing READ_PHONE_STATE permission", e)
                }
            }
        } else {
            val telephonyManager = context.getSystemService(android.content.Context.TELEPHONY_SERVICE) as? TelephonyManager
            if (telephonyManager != null && telephonyManager.simState == android.telephony.TelephonyManager.SIM_STATE_READY) {
                sims.add(
                    SimInfo(
                        slotIndex = 0,
                        subscriptionId = 0,
                        carrierName = telephonyManager.networkOperatorName,
                        phoneNumber = telephonyManager.line1Number,
                        isoCountryCode = telephonyManager.simCountryIso,
                        isActive = true
                    )
                )
            }
        }
        return sims
    }

    fun getSimForSlot(context: Context, slotIndex: String): SimInfo? {
        val slot = slotIndex.toIntOrNull() ?: return null
        return getActiveSims(context).find { it.slotIndex == slot }
    }

    fun getDefaultSubscriptionId(context: Context): Int {
        return if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.LOLLIPOP_MR1) {
            val subscriptionManager = context.getSystemService(android.content.Context.TELEPHONY_SUBSCRIPTION_SERVICE) as? SubscriptionManager
            val defaultSub = SubscriptionManager.getDefaultSubscriptionId()
            if (defaultSub != SubscriptionManager.INVALID_SUBSCRIPTION_ID) defaultSub else 0
        } else {
            0
        }
    }

    fun isDualSim(context: Context): Boolean {
        return getActiveSims(context).size > 1
    }

    fun getNetworkName(context: Context, slotIndex: String): String? {
        return getSimForSlot(context, slotIndex)?.carrierName
    }
}
