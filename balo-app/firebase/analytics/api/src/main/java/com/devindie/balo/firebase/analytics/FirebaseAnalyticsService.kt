package com.devindie.balo.firebase.analytics

interface FirebaseAnalyticsService {
    fun logEvent(name: String, params: Map<String, Any?>? = null)
    fun setUserProperty(name: String, value: String?)
    fun setUserId(userId: String?)
    fun setAnalyticsCollectionEnabled(enabled: Boolean)
    fun resetAnalyticsData()
}
