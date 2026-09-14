package com.mobilemoney.gateway.ussd

import com.mobilemoney.gateway.model.USSDStep

/**
 * Delegates USSD step building to the real implementation in util.USSDExecutor.
 */
object USSDExecutor {
    fun buildMTN(operation: String, slotIndex: String, phone: String, amount: Double, pin: String?): List<USSDStep> {
        return com.mobilemoney.gateway.util.USSDExecutor.buildMTN(operation, slotIndex, phone, amount, pin)
    }

    fun buildAirtel(operation: String, slotIndex: String, phone: String, amount: Double, pin: String?): List<USSDStep> {
        return com.mobilemoney.gateway.util.USSDExecutor.buildAirtel(operation, slotIndex, phone, amount, pin)
    }

    fun buildZamtel(operation: String, slotIndex: String, phone: String, amount: Double, pin: String?): List<USSDStep> {
        return com.mobilemoney.gateway.util.USSDExecutor.buildZamtel(operation, slotIndex, phone, amount, pin)
    }

    fun matchesPattern(text: String, expectedPattern: String?): Boolean {
        return com.mobilemoney.gateway.util.USSDExecutor.matchesPattern(text, expectedPattern)
    }
}
