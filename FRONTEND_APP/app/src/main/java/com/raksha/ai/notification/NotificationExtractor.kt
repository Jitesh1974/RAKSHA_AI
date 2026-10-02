package com.raksha.ai.notification

import android.service.notification.StatusBarNotification
import android.util.Log
import com.raksha.ai.models.SecurityEvent

class NotificationExtractor {
    fun extract(sbn: StatusBarNotification): SecurityEvent? {
        val skipReason = NotificationFilter.skipReason(sbn)
        if (skipReason != null) {
            if (skipReason != "unsupported package") {
                Log.d(TAG, "Skipping notification from ${sbn.packageName}: $skipReason")
            }
            return null
        }

        val event = NotificationParser.parse(sbn)
        if (event.message_text.isBlank() && event.urls.isEmpty() && event.attachments.isEmpty()) {
            Log.d(TAG, "Skipping empty notification from ${sbn.packageName}")
            return null
        }
        return event
    }

    companion object {
        private const val TAG = "RAKSHA"
    }
}
