package com.raksha.ai.network

import android.content.Context
import android.security.keystore.KeyGenParameterSpec
import android.security.keystore.KeyProperties
import android.util.Base64
import java.nio.charset.StandardCharsets
import java.security.KeyStore
import javax.crypto.Cipher
import javax.crypto.KeyGenerator
import javax.crypto.SecretKey
import javax.crypto.spec.GCMParameterSpec

class DeviceCredentialStore(context: Context) {

    private val prefs =
        context.getSharedPreferences(
            "raksha_device_credentials",
            Context.MODE_PRIVATE
        )

    private val keyAlias = "raksha_device_key"
    private val keyStoreType = "AndroidKeyStore"

    fun getOrCreateDeviceId(): String {
        val existing = prefs.getString(KEY_DEVICE_ID, null)

        if (!existing.isNullOrBlank()) {
            return existing
        }

        val id = java.util.UUID.randomUUID().toString()

        prefs.edit()
            .putString(KEY_DEVICE_ID, id)
            .apply()

        return id
    }

    fun saveToken(token: String) {
        prefs.edit()
            .putString(KEY_TOKEN, encrypt(token))
            .apply()
    }

    fun getToken(): String? =
        prefs.getString(KEY_TOKEN, null)
            ?.let(::decrypt)
            ?.takeIf { it.isNotBlank() }

    fun clearToken() {
        prefs.edit()
            .remove(KEY_TOKEN)
            .apply()
    }

    private fun getOrCreateKey(): SecretKey {

        val keyStore = KeyStore
            .getInstance(keyStoreType)
            .apply {
                load(null)
            }

        (keyStore.getKey(keyAlias, null) as? SecretKey)?.let {
            return it
        }

        val generator = KeyGenerator.getInstance(
            KeyProperties.KEY_ALGORITHM_AES,
            keyStoreType
        )

        val spec = KeyGenParameterSpec.Builder(
            keyAlias,
            KeyProperties.PURPOSE_ENCRYPT or
                    KeyProperties.PURPOSE_DECRYPT
        )
            .setBlockModes(KeyProperties.BLOCK_MODE_GCM)
            .setEncryptionPaddings(
                KeyProperties.ENCRYPTION_PADDING_NONE
            )
            .setKeySize(256)
            .build()

        generator.init(spec)

        return generator.generateKey()
    }

    private fun encrypt(value: String): String {

        val cipher = Cipher.getInstance(
            "AES/GCM/NoPadding"
        )

        cipher.init(
            Cipher.ENCRYPT_MODE,
            getOrCreateKey()
        )

        val combined =
            cipher.iv +
                    cipher.doFinal(
                        value.toByteArray(
                            StandardCharsets.UTF_8
                        )
                    )

        return Base64.encodeToString(
            combined,
            Base64.NO_WRAP
        )
    }

    private fun decrypt(value: String): String {

        return try {

            val combined =
                Base64.decode(
                    value,
                    Base64.NO_WRAP
                )

            val iv =
                combined.copyOfRange(0, 12)

            val ciphertext =
                combined.copyOfRange(
                    12,
                    combined.size
                )

            val cipher =
                Cipher.getInstance(
                    "AES/GCM/NoPadding"
                )

            cipher.init(
                Cipher.DECRYPT_MODE,
                getOrCreateKey(),
                GCMParameterSpec(128, iv)
            )

            String(
                cipher.doFinal(ciphertext),
                StandardCharsets.UTF_8
            )

        } catch (_: Exception) {
            ""
        }
    }

    companion object {
        private const val KEY_DEVICE_ID = "device_id"
        private const val KEY_TOKEN = "access_token"
    }
}