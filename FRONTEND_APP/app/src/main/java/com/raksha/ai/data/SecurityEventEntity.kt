package com.raksha.ai.data

import androidx.room.Entity
import androidx.room.PrimaryKey
import com.google.gson.Gson
import com.google.gson.reflect.TypeToken
import com.raksha.ai.models.AnalysisStatus
import com.raksha.ai.models.EvidenceItem
import com.raksha.ai.models.RiskReport
import com.raksha.ai.models.SecurityEvent

@Entity(tableName = "security_events")
data class SecurityEventEntity(
    @PrimaryKey val eventId: String,
    val deviceId: String?,
    val sourceApp: String,
    val sender: String?,
    val messageText: String,
    val urlsJson: String,
    val attachmentsJson: String,
    val eventTimestamp: String,
    val createdAtMs: Long,
    val status: String,
    val riskScore: Double?,
    val riskLevel: String?,
    val scamCategory: String?,
    val explanation: String?,
    val recommendedAction: String?,
    val evidenceJson: String,
    val displayRisk: String,
    val failureReason: String?
) {
    fun toModel(): SecurityEvent = SecurityEvent(
        event_id = eventId,
        device_id = deviceId,
        source_app = sourceApp,
        sender = sender,
        message_text = messageText,
        urls = gson.fromJson(urlsJson, stringListType),
        attachments = gson.fromJson(attachmentsJson, stringListType),
        timestamp = eventTimestamp,
        analysisStatus = AnalysisStatus.valueOf(status),
        riskReport = riskScore?.let {
            RiskReport(
                it, riskLevel.orEmpty(), scamCategory.orEmpty(), explanation.orEmpty(),
                recommendedAction.orEmpty(), gson.fromJson(evidenceJson, evidenceType)
            )
        },
        displayRisk = displayRisk,
        failureReason = failureReason
    )

    companion object {
        private val gson = Gson()
        private val stringListType = object : TypeToken<List<String>>() {}.type
        private val evidenceType = object : TypeToken<List<EvidenceItem>>() {}.type
        fun from(event: SecurityEvent, now: Long = System.currentTimeMillis()) = SecurityEventEntity(
            eventId = event.event_id,
            deviceId = event.device_id,
            sourceApp = event.source_app,
            sender = event.sender,
            messageText = event.message_text,
            urlsJson = gson.toJson(event.urls),
            attachmentsJson = gson.toJson(event.attachments),
            eventTimestamp = event.timestamp,
            createdAtMs = now,
            status = event.analysisStatus.name,
            riskScore = event.riskReport?.risk_score,
            riskLevel = event.riskReport?.risk_level,
            scamCategory = event.riskReport?.scam_category,
            explanation = event.riskReport?.explanation,
            recommendedAction = event.riskReport?.recommended_action,
            evidenceJson = gson.toJson(event.riskReport?.evidence.orEmpty()),
            displayRisk = event.displayRisk,
            failureReason = event.failureReason
        )
    }
}
