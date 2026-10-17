package com.devindie.balo.firebase.analytics

import android.content.Context
import android.os.Bundle
import com.google.firebase.analytics.FirebaseAnalytics

class DefaultFirebaseAnalyticsService(
    context: Context,
    private val analytics: FirebaseAnalytics = FirebaseAnalytics.getInstance(context)
) : FirebaseAnalyticsService {

    override fun logEvent(name: String, params: Map<String, Any?>?) {
        val bundle = params?.let { map ->
            Bundle().apply {
                map.forEach { (key, value) ->
                    when (value) {
                        null -> {}
                        is String -> putString(key, value)
                        is Int -> putInt(key, value)
                        is Long -> putLong(key, value)
                        is Double -> putDouble(key, value)
                        is Float -> putFloat(key, value)
                        is Boolean -> putBoolean(key, value)
                        else -> putString(key, value.toString())
                    }
                }
            }
        }
        analytics.logEvent(name, bundle)
    }

    override fun setUserProperty(name: String, value: String?) {
        analytics.setUserProperty(name, value)
    }

    override fun setUserId(userId: String?) {
        analytics.setUserId(userId)
    }

    override fun setAnalyticsCollectionEnabled(enabled: Boolean) {
        analytics.setAnalyticsCollectionEnabled(enabled)
    }

    override fun resetAnalyticsData() {
        analytics.resetAnalyticsData()
    }
}
