package com.mobilemoney.gateway.model

data class TransactionCommand(
    val transactionId: String,
    val simSlot: String,
    val network: String,
    val operation: String,
    val customerPhone: String,
    val amount: Double,
    val pin: String? = null
)

data class USSDStep(
    val type: String,
    val value: String? = null,
    val expectedPattern: String? = null,
    val simSlot: String? = null
)

data class USSDCommand(
    val network: String,
    val operation: String,
    val slotIndex: String,
    val steps: List<USSDStep>
)

data class SMSWebhookPayload(
    val sender: String,
    val message: String,
    val receivedAt: String? = null
)

data class GatewayStatus(
    val slotIndex: String,
    val status: String,
    val network: String? = null,
    val currentTransactionId: String? = null,
    val lastUpdated: Long = System.currentTimeMillis()
)

data class QueueStatus(
    val simCardId: String,
    val networkName: String,
    val queueLength: Int,
    val currentPosition: Int? = null,
    val status: String
)
