package com.raksha.ai.data

import android.util.Log
import com.raksha.ai.BuildConfig
import com.raksha.ai.models.AnalysisStatus
import com.raksha.ai.models.SecurityEvent
import com.raksha.ai.network.DeviceCredentialStore
import com.raksha.ai.network.DeviceRegistrationRequest
import com.raksha.ai.network.SecurityApi
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map
import kotlinx.coroutines.sync.Mutex
import kotlinx.coroutines.sync.withLock
import retrofit2.HttpException

class SecurityRepository(
    private val dao: SecurityEventDao,
    private val api: SecurityApi,
    private val credentials: DeviceCredentialStore,
) {
    private val writeMutex = Mutex()
    private val registrationMutex = Mutex()
    val events: Flow<List<SecurityEvent>> = dao.observeAll().map { rows -> rows.map { it.toModel() } }

    suspend fun recoverInterrupted() = writeMutex.withLock {
        dao.failPending("Couldn't verify: analysis was interrupted")
        dao.applyRetention(System.currentTimeMillis() - RETENTION_MS)
    }

    private suspend fun ensureRegistered(force: Boolean = false) {
        if (!force && !credentials.getToken().isNullOrBlank()) return
        registrationMutex.withLock {
            if (!force && !credentials.getToken().isNullOrBlank()) return
            val response = api.registerDevice(
                DeviceRegistrationRequest(
                    device_id = credentials.getOrCreateDeviceId(),
                    app_version = BuildConfig.VERSION_NAME,
                )
            )
            credentials.saveToken(response.access_token)
        }
    }

    suspend fun capture(event: SecurityEvent): SecurityEvent {
        val normalizedEvent = event.copy(device_id = credentials.getOrCreateDeviceId())
        writeMutex.withLock { persist(normalizedEvent.copy(analysisStatus = AnalysisStatus.PENDING, displayRisk = "PENDING")) }
        try {
            ensureRegistered()

            val report = try {
                api.analyzeEvent(normalizedEvent)
            } catch (error: HttpException) {
                if (error.code() != 401) throw error

                // The backend may have rotated/revoked the device token, or the
                // app may still contain a token from the pre-JWT authentication
                // implementation. Re-register once and retry the same event.
                credentials.clearToken()
                ensureRegistered(force = true)
                api.analyzeEvent(normalizedEvent)
            }

            val analyzed = normalizedEvent.copy(
                analysisStatus = AnalysisStatus.COMPLETE,
                riskReport = report,
                displayRisk = report.risk_level,
                failureReason = null
            )
            writeMutex.withLock { persist(analyzed) }
            return analyzed
        } catch (cancelled: CancellationException) {
            throw cancelled
        } catch (error: Exception) {
            Log.w(TAG, "Backend analysis failed event_id=${normalizedEvent.event_id} error_type=${error.javaClass.simpleName}")
            val failed = normalizedEvent.copy(
                analysisStatus = AnalysisStatus.FAILED,
                displayRisk = "COULDN'T VERIFY",
                failureReason = boundedReason(error.message)
            )
            writeMutex.withLock { persist(failed) }
            return failed
        }
    }

    suspend fun persist(event: SecurityEvent) {
        dao.upsert(SecurityEventEntity.from(event))
        dao.applyRetention(System.currentTimeMillis() - RETENTION_MS)
    }

    private fun boundedReason(reason: String?): String = (reason ?: "Couldn't verify").take(240)

    companion object {
        private const val TAG = "RAKSHA"
        const val RETENTION_MS = 14L * 24 * 60 * 60 * 1000
    }
}
