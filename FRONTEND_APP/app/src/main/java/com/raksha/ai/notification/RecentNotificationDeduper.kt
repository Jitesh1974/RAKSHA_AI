package com.raksha.ai.notification

import android.app.Notification
import android.os.Bundle
import android.service.notification.StatusBarNotification
import com.raksha.ai.models.SecurityEvent
import java.security.MessageDigest
import java.util.LinkedHashMap
import java.util.Locale

internal class RecentNotificationDeduper(
    private val nowMs: () -> Long = { System.currentTimeMillis() }
) {
    private val seen = object : LinkedHashMap<String, Long>(MAX_ENTRIES, 0.75f, true) {
        override fun removeEldestEntry(eldest: MutableMap.MutableEntry<String, Long>?): Boolean = size > MAX_ENTRIES
    }

    @Synchronized
    fun alreadySeen(sbn: StatusBarNotification, event: SecurityEvent): Boolean {
        val lastMessage = lastStableMessage(sbn).ifBlank { event.message_text }
        val sender = event.sender.orEmpty().trim().lowercase(Locale.US)
        val text = lastMessage.trim().lowercase(Locale.US)
        val fingerprints = listOf(
            "id:${sbn.id}|msg:$text",
            "msg:$sender|$text"
        ).map(::sha256)

        val now = nowMs()
        val iterator = seen.entries.iterator()
        while (iterator.hasNext()) {
            if (now - iterator.next().value > WINDOW_MS) iterator.remove()
        }

        if (fingerprints.any { fingerprint -> seen[fingerprint]?.let { now - it <= WINDOW_MS } == true }) {
            return true
        }
        fingerprints.forEach { seen[it] = now }
        return false
    }

    @Suppress("DEPRECATION")
    private fun lastStableMessage(sbn: StatusBarNotification): String {
        val extras: Bundle = sbn.notification.extras
        val messages = extras.getParcelableArray(Notification.EXTRA_MESSAGES)
        if (messages != null) {
            for (index in messages.indices.reversed()) {
                val bundle = messages[index] as? Bundle ?: continue
                val body = bundle.getCharSequence("text")?.toString()?.trim().orEmpty()
                if (body.isNotEmpty()) return body
            }
        }
        return extras.getCharSequence(Notification.EXTRA_TEXT)?.toString()?.trim().orEmpty()
    }

    private fun sha256(value: String): String = MessageDigest.getInstance("SHA-256")
        .digest(value.toByteArray(Charsets.UTF_8))
        .joinToString("") { "%02x".format(it) }

    companion object {
        const val WINDOW_MS = 15_000L
        private const val MAX_ENTRIES = 100
    }
}
