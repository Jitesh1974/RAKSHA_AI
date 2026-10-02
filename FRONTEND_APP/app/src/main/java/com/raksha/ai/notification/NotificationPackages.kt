package com.raksha.ai.notification

object NotificationPackages {
    const val WHATSAPP = "com.whatsapp"
    const val GOOGLE_MESSAGES = "com.google.android.apps.messaging"
    const val SAMSUNG_MESSAGES = "com.samsung.android.messaging"

    val SUPPORTED = setOf(WHATSAPP, GOOGLE_MESSAGES, SAMSUNG_MESSAGES)
}
