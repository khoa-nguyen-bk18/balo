package com.devindie.balo.firebase.performance

import com.google.firebase.perf.FirebasePerformance
import com.google.firebase.perf.metrics.Trace

class DefaultFirebasePerformanceService(
    private val performance: FirebasePerformance = FirebasePerformance.getInstance()
) : FirebasePerformanceService {

    override fun startTrace(traceName: String): TraceHandle {
        val trace = performance.newTrace(traceName)
        trace.start()
        return FirebaseTraceHandle(trace)
    }

    override fun setPerformanceCollectionEnabled(enabled: Boolean) {
        performance.isPerformanceCollectionEnabled = enabled
    }

    private class FirebaseTraceHandle(private val trace: Trace) : TraceHandle {
        override fun putAttribute(attribute: String, value: String) {
            trace.putAttribute(attribute, value)
        }

        override fun getAttribute(attribute: String): String? {
            return trace.getAttribute(attribute)
        }

        override fun removeAttribute(attribute: String) {
            trace.removeAttribute(attribute)
        }

        override fun putMetric(metricName: String, value: Long) {
            trace.putMetric(metricName, value)
        }

        override fun incrementMetric(metricName: String, incrementBy: Long) {
            trace.incrementMetric(metricName, incrementBy)
        }

        override fun getLongMetric(metricName: String): Long {
            return trace.getLongMetric(metricName)
        }

        override fun stop() {
            trace.stop()
        }
    }
}
