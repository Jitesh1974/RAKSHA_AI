package com.raksha.ai.network

import com.raksha.ai.BuildConfig

object NetworkConfig {
    val BASE_URL: String = BuildConfig.BACKEND_BASE_URL.ensureTrailingSlash()
    val GOOGLE_WEB_CLIENT_ID: String = BuildConfig.GOOGLE_WEB_CLIENT_ID
    val IS_RELEASE: Boolean = !BuildConfig.BUILD_TYPE.equals("debug", ignoreCase = true)

    private fun String.ensureTrailingSlash(): String = if (endsWith('/')) this else "$this/"
}
