package com.devindie.balo.firebase.performance

interface FirebasePerformanceService {
    fun startTrace(traceName: String): TraceHandle
    fun setPerformanceCollectionEnabled(enabled: Boolean)
}

inline fun <T> FirebasePerformanceService.trace(traceName: String, block: (TraceHandle) -> T): T {
    val traceHandle = startTrace(traceName)
    return try {
        block(traceHandle)
    } finally {
        traceHandle.stop()
    }
}
