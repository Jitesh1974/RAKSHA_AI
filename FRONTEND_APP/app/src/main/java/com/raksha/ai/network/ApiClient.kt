package com.raksha.ai.network

import android.content.Context
import android.util.Log
import com.google.gson.GsonBuilder
import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import java.util.concurrent.TimeUnit

object ApiClient {
    @Volatile private var initialized = false
    lateinit var securityApi: SecurityApi
        private set

    fun init(context: Context) {
        if (initialized) return
        synchronized(this) {
            if (initialized) return
            val credentials = DeviceCredentialStore(context.applicationContext)
            val httpLogger = HttpLoggingInterceptor { message -> Log.d("RAKSHA_HTTP", message) }.apply {
                level = if (com.raksha.ai.BuildConfig.DEBUG) HttpLoggingInterceptor.Level.BASIC else HttpLoggingInterceptor.Level.NONE
            }
            val okHttpClient = OkHttpClient.Builder()
                .connectTimeout(10, TimeUnit.SECONDS)
                .readTimeout(75, TimeUnit.SECONDS)
                .writeTimeout(15, TimeUnit.SECONDS)
                .addInterceptor(DeviceAuthInterceptor(credentials))
                .addInterceptor(httpLogger)
                .build()
            val gson = GsonBuilder().serializeNulls().create()
            securityApi = Retrofit.Builder()
                .baseUrl(NetworkConfig.BASE_URL)
                .client(okHttpClient)
                .addConverterFactory(GsonConverterFactory.create(gson))
                .build()
                .create(SecurityApi::class.java)
            initialized = true
        }
    }
}
