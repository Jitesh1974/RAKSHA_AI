package com.raksha.ai.notification

import android.app.Notification
import android.service.notification.StatusBarNotification

object NotificationFilter {
    private val backgroundWorkText = Regex(
        """doing work in (the )?background|checking for (new )?messages|syncing|synchroniz|messages are doing work""",
        RegexOption.IGNORE_CASE
    )

    private val callText = Regex(
        """incoming (group )?(voice|video) call|ongoing (group )?(voice|video) call|missed (group )?(voice|video) call|whatsapp (voice|video )?call|\bis calling\b|\bring\b|\bcalling[.…]*$""",
        RegexOption.IGNORE_CASE
    )

    private val summaryText = Regex(
        """\b\d+\s+(new\s+)?messages?\b""",
        RegexOption.IGNORE_CASE
    )

    private val systemEventText = Regex(
        """created (this )?group|added you|removed you|left the group|you're now an admin|changed the group""",
        RegexOption.IGNORE_CASE
    )

    private val callAction = Regex(
        """^(answer|decline|reject|hang up|hangup)$""",
        RegexOption.IGNORE_CASE
    )

    fun skipReason(sbn: StatusBarNotification): String? {
        if (sbn.packageName !in NotificationPackages.SUPPORTED) {
            return "unsupported package"
        }

        val notification = sbn.notification
        val extras = notification.extras
        val category = notification.category
        val channelId = notification.channelId.orEmpty()
        val tag = sbn.tag.orEmpty()
        val template = extras.getString(Notification.EXTRA_TEMPLATE).orEmpty()
        val title = extras.getCharSequence(Notification.EXTRA_TITLE)?.toString().orEmpty()
        val text = extras.getCharSequence(Notification.EXTRA_TEXT)?.toString().orEmpty()
        val summary = extras.getCharSequence(Notification.EXTRA_SUMMARY_TEXT)?.toString().orEmpty()
        val combined = "$title $text $summary"

        if (sbn.isOngoing || (notification.flags and Notification.FLAG_ONGOING_EVENT != 0)) {
            return "ongoing service notification"
        }
        if (!sbn.isClearable) return "non-clearable notification"

        if (category == Notification.CATEGORY_SERVICE ||
            category == Notification.CATEGORY_PROGRESS ||
            category == Notification.CATEGORY_STATUS ||
            category == Notification.CATEGORY_SYSTEM
        ) {
            return "service/progress/status category"
        }

        if (channelId.contains("foreground", ignoreCase = true) ||
            channelId.contains("background", ignoreCase = true) ||
            channelId.contains("sync", ignoreCase = true)
        ) {
            return "background/sync channel"
        }

        if (backgroundWorkText.containsMatchIn(combined)) return "background work text"

        if (category == Notification.CATEGORY_CALL || category == Notification.CATEGORY_MISSED_CALL) {
            return "call category"
        }
        if (notification.fullScreenIntent != null) return "full-screen call UI"
        if (template.contains("CallStyle", ignoreCase = true)) return "CallStyle template"
        if (hasCallAction(notification)) return "call action buttons"

        if (notification.flags and Notification.FLAG_GROUP_SUMMARY != 0) return "group summary"
        if (channelId.contains("call", ignoreCase = true) ||
            channelId.contains("voip", ignoreCase = true) ||
            channelId.contains("ringing", ignoreCase = true)
        ) return "call channel"
        if (tag.contains("call", ignoreCase = true) || tag.contains("voip", ignoreCase = true)) {
            return "call tag"
        }
        if (callText.containsMatchIn(combined)) return "call-like text"
        if (summaryText.containsMatchIn(combined) || summaryText.containsMatchIn(summary)) return "summary notification"
        if (systemEventText.containsMatchIn(combined)) return "non-message system event"

        return null
    }

    private fun hasCallAction(notification: Notification): Boolean {
        val actions = notification.actions ?: return false
        return actions.any { action ->
            callAction.containsMatchIn(action.title?.toString()?.trim().orEmpty())
        }
    }
}
