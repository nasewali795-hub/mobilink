package com.mobilemoney.gateway.util

import android.util.Log
import com.mobilemoney.gateway.model.USSDStep
import java.util.regex.Pattern

/**
 * Zambia Mobile Money USSD Step Builder
 *
 * Verified USSD Codes (Zambia):
 * ─────────────────────────────────────────────────────
 * MTN MoMo    → Balance: *115#  (menu: 6 → 1)
 * Airtel Money→ Balance: *778#  (menu: 4 → 1)
 * Zamtel Kwac → Balance: *200#  (menu: 5 → 1)
 * ─────────────────────────────────────────────────────
 */
object USSDExecutor {
    private const val TAG = "USSDExecutor"

    // ─── MTN ZAMBIA (*115#) ──────────────────────────────────────────────────
    fun buildMTN(operation: String, slotIndex: String, phoneNumber: String, amount: Double, pin: String?): List<USSDStep> {
        return when {
            operation.equals("balance", true) -> mutableListOf(
                // MTN MoMo balance: *115# → 9 (My Account) → 1 → 1 → PIN
                USSDStep("ussd", "*115#", null, slotIndex),
                USSDStep("ussd_response", null, "(?i)select|menu|option|MoMo"),
                USSDStep("ussd_input", "9"),
                USSDStep("ussd_response", null, "(?i)select|account|option"),
                USSDStep("ussd_input", "1"),
                USSDStep("ussd_response", null, "(?i)select|option|confirm"),
                USSDStep("ussd_input", "1"),
                USSDStep("ussd_response", null, "(?i)pin|secret|password|enter.*pin"),
                USSDStep("ussd_input", pin.orEmpty()),
                USSDStep("ussd_response", null, "(?i)balance|kwacha|ZMW|K\\s*[\\d,]+|your.*balance")
            )
            operation.equals("cash_out", true) -> mutableListOf(
                // MTN MoMo send money: *115# → 1 (Send Money)
                USSDStep("ussd", "*115#", null, slotIndex),
                USSDStep("ussd_response", null, "(?i)send money|transfer|menu"),
                USSDStep("ussd_input", "1"),
                USSDStep("ussd_response", null, "(?i)enter.*number|phone|recipient|mobile"),
                USSDStep("ussd_input", phoneNumber),
                USSDStep("ussd_response", null, "(?i)amount|enter amount|how much"),
                USSDStep("ussd_input", amount.toInt().toString()),
                USSDStep("ussd_response", null, "(?i)PIN|password|secret|enter.*pin"),
                USSDStep("ussd_input", pin.orEmpty())
            )
            else -> mutableListOf(
                // MTN MoMo cash in / deposit: *115# → 5 (Cash In)
                USSDStep("ussd", "*115#", null, slotIndex),
                USSDStep("ussd_response", null, "(?i)cash in|deposit|receive|menu"),
                USSDStep("ussd_input", "5"),
                USSDStep("ussd_response", null, "(?i)agent.*number|enter.*number|phone"),
                USSDStep("ussd_input", phoneNumber),
                USSDStep("ussd_response", null, "(?i)amount|enter amount|how much"),
                USSDStep("ussd_input", amount.toInt().toString())
            )
        }
    }

    // ─── AIRTEL ZAMBIA (*778#) ───────────────────────────────────────────────
    fun buildAirtel(operation: String, slotIndex: String, phoneNumber: String, amount: Double, pin: String?): List<USSDStep> {
        return when {
            operation.equals("balance", true) -> mutableListOf(
                // Airtel Money balance: *778# → 4 (My Account) → 1 (Balance Enquiry)
                USSDStep("ussd", "*778#", null, slotIndex),
                USSDStep("ussd_response", null, "(?i)my account|menu|select|airtel"),
                USSDStep("ussd_input", "4"),
                USSDStep("ussd_response", null, "(?i)balance|mini statement|account info"),
                USSDStep("ussd_input", "1"),
                USSDStep("ussd_response", null, "(?i)balance|kwacha|ZMW|K\\s*[\\d,]+|your.*balance")
            )
            operation.equals("cash_out", true) -> mutableListOf(
                // Airtel Money send: *778# → 1 (Send Money)
                USSDStep("ussd", "*778#", null, slotIndex),
                USSDStep("ussd_response", null, "(?i)send money|transfer|menu"),
                USSDStep("ussd_input", "1"),
                USSDStep("ussd_response", null, "(?i)enter.*number|phone|recipient|mobile"),
                USSDStep("ussd_input", phoneNumber),
                USSDStep("ussd_response", null, "(?i)amount|enter amount|how much"),
                USSDStep("ussd_input", amount.toInt().toString()),
                USSDStep("ussd_response", null, "(?i)PIN|password|secret|enter.*pin"),
                USSDStep("ussd_input", pin.orEmpty())
            )
            else -> mutableListOf(
                // Airtel Money cash in: *778# → 2 (Cash In)
                USSDStep("ussd", "*778#", null, slotIndex),
                USSDStep("ussd_response", null, "(?i)cash in|deposit|receive|menu"),
                USSDStep("ussd_input", "2"),
                USSDStep("ussd_response", null, "(?i)agent.*number|enter.*number|phone"),
                USSDStep("ussd_input", phoneNumber),
                USSDStep("ussd_response", null, "(?i)amount|enter amount|how much"),
                USSDStep("ussd_input", amount.toInt().toString())
            )
        }
    }

    // ─── ZAMTEL KWACHA (*200#) ───────────────────────────────────────────────
    fun buildZamtel(operation: String, slotIndex: String, phoneNumber: String, amount: Double, pin: String?): List<USSDStep> {
        return when {
            operation.equals("balance", true) -> mutableListOf(
                // Zamtel Kwacha balance: *200# → 5 (My Account) → 1 (Check Balance)
                USSDStep("ussd", "*200#", null, slotIndex),
                USSDStep("ussd_response", null, "(?i)my account|menu|select|kwacha"),
                USSDStep("ussd_input", "5"),
                USSDStep("ussd_response", null, "(?i)balance|mini statement|account"),
                USSDStep("ussd_input", "1"),
                USSDStep("ussd_response", null, "(?i)balance|kwacha|ZMW|K\\s*[\\d,]+|your.*balance")
            )
            operation.equals("cash_out", true) -> mutableListOf(
                // Zamtel Kwacha send: *200# → 1 (Send Money)
                USSDStep("ussd", "*200#", null, slotIndex),
                USSDStep("ussd_response", null, "(?i)send money|transfer|menu"),
                USSDStep("ussd_input", "1"),
                USSDStep("ussd_response", null, "(?i)enter.*number|phone|recipient|mobile"),
                USSDStep("ussd_input", phoneNumber),
                USSDStep("ussd_response", null, "(?i)amount|enter amount|how much"),
                USSDStep("ussd_input", amount.toInt().toString()),
                USSDStep("ussd_response", null, "(?i)PIN|password|secret|enter.*pin"),
                USSDStep("ussd_input", pin.orEmpty())
            )
            else -> mutableListOf(
                // Zamtel Kwacha cash in: *200# → 3 (Cash In)
                USSDStep("ussd", "*200#", null, slotIndex),
                USSDStep("ussd_response", null, "(?i)cash in|deposit|receive|menu"),
                USSDStep("ussd_input", "3"),
                USSDStep("ussd_response", null, "(?i)agent.*number|enter.*number|phone"),
                USSDStep("ussd_input", phoneNumber),
                USSDStep("ussd_response", null, "(?i)amount|enter amount|how much"),
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
