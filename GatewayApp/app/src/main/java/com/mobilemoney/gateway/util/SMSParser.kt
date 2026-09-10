package com.mobilemoney.gateway.util

import android.util.Log
import java.util.regex.Pattern

object SMSParser {
    private const val TAG = "SMSParser"

    private val FAILURE_INDICATORS = listOf(
        "failed", "unsuccessful", "declined", "insufficient", "timeout", "error",
        "not allowed", "invalid", "incorrect", "rejected", "could not"
    )

    private val PATTERNS = listOf(
        mapOf(
            "network" to "MTN",
            "success_pattern" to "(?:transaction\\s+(?:id|ref)[:\\s]+)?([A-Z0-9]{8,20})",
            "amount_pattern" to "(?:amount|amt)[:\\s]+(?:K|ZMW|MWK)?\\s*([\\d,]+\\.?\\d*)",
            "balance_pattern" to "(?:new\\s+balance|bal)[:\\s]+(?:K|ZMW|MWK)?\\s*([\\d,]+\\.?\\d*)"
        ),
        mapOf(
            "network" to "Airtel",
            "success_pattern" to "(?:transaction\\s+(?:id|ref)[:\\s]+)?([A-Z0-9]{8,20})",
            "amount_pattern" to "(?:amount|amt)[:\\s]+(?:K|ZMW|MWK)?\\s*([\\d,]+\\.?\\d*)",
            "balance_pattern" to "(?:new\\s+balance|bal)[:\\s]+(?:K|ZMW|MWK)?\\s*([\\d,]+\\.?\\d*)"
        ),
        mapOf(
            "network" to "Zamtel",
            "success_pattern" to "(?:transaction\\s+(?:id|ref)[:\\s]+)?([A-Z0-9]{8,20})",
            "amount_pattern" to "(?:amount|amt)[:\\s]+(?:K|ZMW|MWK)?\\s*([\\d,]+\\.?\\d*)",
            "balance_pattern" to "(?:new\\s+balance|bal)[:\\s]+(?:K|ZMW|MWK)?\\s*([\\d,]+\\.?\\d*)"
        )
    )

    data class ParsedSMS(
        val transactionId: String?,
        val amount: Double?,
        val newBalance: Double?,
        val reference: String?,
        val status: String,
        val rawMessage: String,
        val sender: String? = null
    )

    fun parse(message: String, sender: String? = null): ParsedSMS {
        val lower = message.lowercase()
        val isFailure = FAILURE_INDICATORS.any { lower.contains(it) }

        if (isFailure) {
            return ParsedSMS(
                transactionId = null,
                amount = null,
                newBalance = null,
                reference = null,
                status = "failed",
                rawMessage = message,
                sender = sender
            )
        }

        val transactionId = extract(message, "success_pattern")
        val amount = extractAmount(message)
        val newBalance = extractBalance(message)
        val status = if (transactionId != null || amount != null || newBalance != null) "success" else "unrecognized"

        return ParsedSMS(
            transactionId = transactionId,
            amount = amount,
            newBalance = newBalance,
            reference = transactionId,
            status = status,
            rawMessage = message,
            sender = sender
        )
    }

    fun isMnoNotification(message: String): Boolean {
        val keywords = listOf(
            "transaction", "received", "sent", "balance", "airtime", "mobile money",
            "mtn", "airtel", "zamtel", "mno", "payment", "confirmed"
        )
        val lower = message.lowercase()
        return keywords.any { lower.contains(it) }
    }

    private fun extract(message: String, key: String): String? {
        for (patternDef in PATTERNS) {
            val pattern = patternDef[key] as? String ?: continue
            val matcher = Pattern.compile(pattern, Pattern.CASE_INSENSITIVE).matcher(message)
            if (matcher.find()) {
                return matcher.group(1)?.trim()
            }
        }
        return null
    }

    private fun extractAmount(message: String): Double? {
        for (patternDef in PATTERNS) {
            val pattern = patternDef["amount_pattern"] as? String ?: continue
            val matcher = Pattern.compile(pattern, Pattern.CASE_INSENSITIVE).matcher(message)
            if (matcher.find()) {
                val raw = matcher.group(1)?.replace(",", "")
                return raw?.toDoubleOrNull()
            }
        }
        val generic = Pattern.compile("(?:K|ZMW|MWK)?\\s*([\\d,]+\\.?\\d*)", Pattern.CASE_INSENSITIVE).matcher(message)
        if (generic.find()) {
            return generic.group(1)?.replace(",", "")?.toDoubleOrNull()
        }
        return null
    }

    private fun extractBalance(message: String): Double? {
        for (patternDef in PATTERNS) {
            val pattern = patternDef["balance_pattern"] as? String ?: continue
            val matcher = Pattern.compile(pattern, Pattern.CASE_INSENSITIVE).matcher(message)
            if (matcher.find()) {
                val raw = matcher.group(1)?.replace(",", "")
                return raw?.toDoubleOrNull()
            }
        }
        return null
    }
}
