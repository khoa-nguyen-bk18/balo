package com.devindie.balo.firebase.phone

import android.app.Activity
import com.devindie.balo.firebase.phone.model.PhoneVerificationState
import kotlinx.coroutines.flow.Flow

interface FirebasePhoneVerificationService {
    fun verifyPhoneNumber(
        activity: Activity,
        phoneNumber: String,
        timeoutSeconds: Long = 60L
    ): Flow<PhoneVerificationState>

    fun resendVerificationCode(
        activity: Activity,
        phoneNumber: String,
        resendToken: Any?,
        timeoutSeconds: Long = 60L
    ): Flow<PhoneVerificationState>
}
