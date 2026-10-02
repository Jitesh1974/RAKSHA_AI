package com.raksha.ai.network

import okhttp3.Interceptor
import okhttp3.Response

class DeviceAuthInterceptor(private val credentials: DeviceCredentialStore) : Interceptor {
    override fun intercept(chain: Interceptor.Chain): Response {
        val request = chain.request()
        val builder = request.newBuilder()
            .header("X-Device-ID", credentials.getOrCreateDeviceId())
        credentials.getToken()?.let { builder.header("Authorization", "Bearer $it") }
        return chain.proceed(builder.build())
    }
}
