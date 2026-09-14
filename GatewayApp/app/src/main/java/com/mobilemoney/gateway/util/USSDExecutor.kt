package com.mobilemoney.gateway.util

import android.util.Log
import com.mobilemoney.gateway.model.USSDStep
import java.util.regex.Pattern

object USSDExecutor {
    private const val TAG = "USSDExecutor"

    fun buildMTN(operation: String, slotIndex: String, phoneNumber: String, amount: Double, pin: String?): List<USSDStep> {
        return when {
            operation.equals("balance", true) -> mutableListOf(
                // MTN Zambia balance check: dial *115# → single-step, response contains balance
                USSDStep("ussd", "*115#", null, slotIndex),
                USSDStep("ussd_response", null, "(?i)balance|kwacha|ZMW|K\\s*[\\d,]+|your.*balance|MoMo)")
            )
            operation.equals("cash_out", true) -> mutableListOf(
                USSDStep("ussd", "*115#", null, slotIndex),
                USSDStep("ussd_response", null, "(?:Send Money|Transfer|menu)"),
                USSDStep("ussd_input", "1"),
                USSDStep("ussd_response", null, "(?:Enter.*number|Phone|recipient)"),
                USSDStep("ussd_input", phoneNumber),
                USSDStep("ussd_response", null, "(?:amount|Enter|how much)"),
                USSDStep("ussd_input", amount.toInt().toString()),
                USSDStep("ussd_response", null, "(?:PIN|password|secret)"),
                USSDStep("ussd_input", pin.orEmpty())
            )
            else -> mutableListOf(
                // cash_in / deposit
                USSDStep("ussd", "*115#", null, slotIndex),
                USSDStep("ussd_response", null, "(?:Receive Money|Deposit|menu)"),
                USSDStep("ussd_input", "5"),
                USSDStep("ussd_response", null, "(?:Enter.*number|Phone|agent)"),
                USSDStep("ussd_input", phoneNumber),
                USSDStep("ussd_response", null, "(?:amount|Enter|how much)"),
                USSDStep("ussd_input", amount.toInt().toString())
            )
        }
    }

    fun buildAirtel(operation: String, slotIndex: String, phoneNumber: String, amount: Double, pin: String?): List<USSDStep> {
        return if (operation.equals("cash_out", true)) {
            mutableListOf(
                USSDStep("ussd", "*115#", null, slotIndex),
                USSDStep("ussd_response", null, "(?:Send Money|Transfer)"),
                USSDStep("ussd_input", "1"),
                USSDStep("ussd_response", null, "(?:Enter.*number|Phone)"),
                USSDStep("ussd_input", phoneNumber),
                USSDStep("ussd_response", null, "(?:amount|Enter)"),
                USSDStep("ussd_input", amount.toInt().toString()),
                USSDStep("ussd_response", null, "(?:PIN|password)"),
                USSDStep("ussd_input", pin.orEmpty())
            )
        } else {
            mutableListOf(
                USSDStep("ussd", "*114#", null, slotIndex),
                USSDStep("ussd_response", null, "(?:Receive Money|Deposit)"),
                USSDStep("ussd_input", "1"),
                USSDStep("ussd_response", null, "(?:Enter.*number|Phone)"),
                USSDStep("ussd_input", phoneNumber),
                USSDStep("ussd_response", null, "(?:amount|Enter)"),
                USSDStep("ussd_input", amount.toInt().toString())
            )
        }
    }

    fun buildZamtel(operation: String, slotIndex: String, phoneNumber: String, amount: Double, pin: String?): List<USSDStep> {
        return if (operation.equals("cash_out", true)) {
            mutableListOf(
                USSDStep("ussd", "*811#", null, slotIndex),
                USSDStep("ussd_response", null, "(?:Send Money|Transfer)"),
                USSDStep("ussd_input", "1"),
                USSDStep("ussd_response", null, "(?:Enter.*number|Phone)"),
                USSDStep("ussd_input", phoneNumber),
                USSDStep("ussd_response", null, "(?:amount|Enter)"),
                USSDStep("ussd_input", amount.toInt().toString()),
                USSDStep("ussd_response", null, "(?:PIN|password)"),
                USSDStep("ussd_input", pin.orEmpty())
            )
        } else {
            mutableListOf(
                USSDStep("ussd", "*810#", null, slotIndex),
                USSDStep("ussd_response", null, "(?:Receive Money|Deposit)"),
                USSDStep("ussd_input", "1"),
                USSDStep("ussd_response", null, "(?:Enter.*number|Phone)"),
                USSDStep("ussd_input", phoneNumber),
                USSDStep("ussd_response", null, "(?:amount|Enter)"),
                USSDStep("ussd_input", amount.toInt().toString())
            )
        }
    }

    fun matchesPattern(text: String?, expectedPattern: String?): Boolean {
        if (text.isNullOrBlank() || expectedPattern.isNullOrBlank()) return false
        return try {
            Pattern.compile(expectedPattern, Pattern.CASE_INSENSITIVE).matcher(text).find()
        } catch (e: Exception) {
            Log.w(TAG, "Invalid regex pattern: $expectedPattern", e)
            false
        }
    }
}
