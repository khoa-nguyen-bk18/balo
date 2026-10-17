package com.devindie.balo.firebase.phone.model

sealed interface PhoneVerificationState {
    data class CodeSent(
        val verificationId: String,
        val token: Any?
    ) : PhoneVerificationState

    data class VerificationCompleted(
        val smsCode: String? = null
    ) : PhoneVerificationState

    data class VerificationFailed(
        val error: Throwable
    ) : PhoneVerificationState

    data class CodeAutoRetrievalTimeout(
        val verificationId: String
    ) : PhoneVerificationState
}
