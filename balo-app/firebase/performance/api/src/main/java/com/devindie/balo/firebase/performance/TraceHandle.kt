package com.devindie.balo.firebase.performance

interface TraceHandle {
    fun putAttribute(attribute: String, value: String)
    fun getAttribute(attribute: String): String?
    fun removeAttribute(attribute: String)
    fun putMetric(metricName: String, value: Long)
    fun incrementMetric(metricName: String, incrementBy: Long = 1)
    fun getLongMetric(metricName: String): Long
    fun stop()
}
