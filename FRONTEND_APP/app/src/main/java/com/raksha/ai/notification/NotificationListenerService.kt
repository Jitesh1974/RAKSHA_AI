package com.raksha.ai.notification

import android.service.notification.NotificationListenerService
import android.service.notification.StatusBarNotification
import android.util.Log
import com.raksha.ai.data.RakshaApplication
import com.raksha.ai.ui.alerts.AlertDeliveryManager
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.cancel
import kotlinx.coroutines.launch

class RakshaNotificationListenerService : NotificationListenerService() {

    private val serviceScope = CoroutineScope(SupervisorJob() + Dispatchers.IO)
    private val extractor = NotificationExtractor()
    private val deduper = RecentNotificationDeduper()

    override fun onNotificationPosted(sbn: StatusBarNotification) {
        val event = extractor.extract(sbn) ?: return
        if (deduper.alreadySeen(sbn, event)) {
            Log.d(TAG, "Skipping duplicate notification event=${event.event_id}")
            return
        }
        analyzeInBackground(event)
    }

    override fun onDestroy() {
        serviceScope.cancel()
        super.onDestroy()
    }

    private fun analyzeInBackground(event: com.raksha.ai.models.SecurityEvent) {
        serviceScope.launch {
            try {
                val app = application as RakshaApplication
                val result = app.repository.capture(event)
                AlertDeliveryManager(applicationContext, app.settingsStore).showAnalysisResult(result)
            } catch (error: Exception) {
                Log.e(TAG, "Event analysis pipeline failed for id=${event.event_id}", error)
            }
        }
    }

    companion object {
        private const val TAG = "RAKSHA"
        const val WHATSAPP_PACKAGE = NotificationPackages.WHATSAPP
        const val GOOGLE_MESSAGES_PACKAGE = NotificationPackages.GOOGLE_MESSAGES
        const val SAMSUNG_MESSAGES_PACKAGE = NotificationPackages.SAMSUNG_MESSAGES
        val SUPPORTED_PACKAGES = NotificationPackages.SUPPORTED
    }
}
