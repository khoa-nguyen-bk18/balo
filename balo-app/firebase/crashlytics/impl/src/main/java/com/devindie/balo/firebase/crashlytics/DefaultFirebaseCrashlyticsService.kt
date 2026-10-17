package com.devindie.balo.firebase.crashlytics

import com.google.firebase.crashlytics.FirebaseCrashlytics

class DefaultFirebaseCrashlyticsService(
    private val crashlytics: FirebaseCrashlytics = FirebaseCrashlytics.getInstance()
) : FirebaseCrashlyticsService {

    override fun recordException(throwable: Throwable) {
        crashlytics.recordException(throwable)
    }

    override fun log(message: String) {
        crashlytics.log(message)
    }

    override fun setCustomKey(key: String, value: String) {
        crashlytics.setCustomKey(key, value)
    }

    override fun setCustomKey(key: String, value: Boolean) {
        crashlytics.setCustomKey(key, value)
    }

    override fun setCustomKey(key: String, value: Int) {
        crashlytics.setCustomKey(key, value)
    }

    override fun setCustomKey(key: String, value: Long) {
        crashlytics.setCustomKey(key, value)
    }

    override fun setCustomKey(key: String, value: Double) {
        crashlytics.setCustomKey(key, value)
    }

    override fun setCustomKey(key: String, value: Float) {
        crashlytics.setCustomKey(key, value)
    }

    override fun setUserId(userId: String) {
        crashlytics.setUserId(userId)
    }

    override fun setCrashlyticsCollectionEnabled(enabled: Boolean) {
        crashlytics.setCrashlyticsCollectionEnabled(enabled)
    }
}
