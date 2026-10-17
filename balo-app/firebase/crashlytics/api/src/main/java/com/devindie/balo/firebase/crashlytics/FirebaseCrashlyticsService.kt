package com.devindie.balo.firebase.crashlytics

interface FirebaseCrashlyticsService {
    fun recordException(throwable: Throwable)
    fun log(message: String)
    fun setCustomKey(key: String, value: String)
    fun setCustomKey(key: String, value: Boolean)
    fun setCustomKey(key: String, value: Int)
    fun setCustomKey(key: String, value: Long)
    fun setCustomKey(key: String, value: Double)
    fun setCustomKey(key: String, value: Float)
    fun setUserId(userId: String)
    fun setCrashlyticsCollectionEnabled(enabled: Boolean)
}
