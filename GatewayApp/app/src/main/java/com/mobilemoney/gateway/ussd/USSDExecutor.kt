package com.mobilemoney.gateway.ussd

import com.mobilemoney.gateway.model.USSDStep

object USSDExecutor {
    fun buildMTN(operation: String, slotIndex: String, phone: String, amount: Double, pin: String?): List<USSDStep> {
        // Placeholder for MTN USSD steps
        return emptyList()
    }

    fun buildAirtel(operation: String, slotIndex: String, phone: String, amount: Double, pin: String?): List<USSDStep> {
        // Placeholder for Airtel USSD steps
        return emptyList()
    }

    fun buildZamtel(operation: String, slotIndex: String, phone: String, amount: Double, pin: String?): List<USSDStep> {
        // Placeholder for Zamtel USSD steps
        return emptyList()
    }

    fun matchesPattern(text: String, expectedPattern: String?): Boolean {
        if (expectedPattern == null) return false
        val regex = Regex(expectedPattern, RegexOption.IGNORE_CASE)
        return regex.containsMatchIn(text)
    }
}
