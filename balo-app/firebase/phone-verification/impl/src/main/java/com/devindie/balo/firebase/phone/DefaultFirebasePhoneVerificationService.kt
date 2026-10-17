package com.devindie.balo.firebase.phone

import android.app.Activity
import com.devindie.balo.firebase.phone.model.PhoneVerificationState
import com.google.firebase.FirebaseException
import com.google.firebase.auth.FirebaseAuth
import com.google.firebase.auth.PhoneAuthCredential
import com.google.firebase.auth.PhoneAuthOptions
import com.google.firebase.auth.PhoneAuthProvider
import kotlinx.coroutines.channels.awaitClose
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.callbackFlow
import java.util.concurrent.TimeUnit

class DefaultFirebasePhoneVerificationService(
    private val auth: FirebaseAuth = FirebaseAuth.getInstance()
) : FirebasePhoneVerificationService {

    override fun verifyPhoneNumber(
        activity: Activity,
        phoneNumber: String,
        timeoutSeconds: Long
    ): Flow<PhoneVerificationState> = callbackFlow {
        val callbacks = object : PhoneAuthProvider.OnVerificationStateChangedCallbacks() {
            override fun onVerificationCompleted(credential: PhoneAuthCredential) {
                trySend(PhoneVerificationState.VerificationCompleted(credential.smsCode))
            }

            override fun onVerificationFailed(e: FirebaseException) {
                trySend(PhoneVerificationState.VerificationFailed(e))
            }

            override fun onCodeSent(
                verificationId: String,
                token: PhoneAuthProvider.ForceResendingToken
            ) {
                trySend(PhoneVerificationState.CodeSent(verificationId, token))
            }

            override fun onCodeAutoRetrievalTimeOut(verificationId: String) {
                trySend(PhoneVerificationState.CodeAutoRetrievalTimeout(verificationId))
            }
        }

        val options = PhoneAuthOptions.newBuilder(auth)
            .setPhoneNumber(phoneNumber)
            .setTimeout(timeoutSeconds, TimeUnit.SECONDS)
            .setActivity(activity)
            .setCallbacks(callbacks)
            .build()

        PhoneAuthProvider.verifyPhoneNumber(options)

        awaitClose { /* Cleanup if required */ }
    }

    override fun resendVerificationCode(
        activity: Activity,
        phoneNumber: String,
        resendToken: Any?,
        timeoutSeconds: Long
    ): Flow<PhoneVerificationState> = callbackFlow {
        val callbacks = object : PhoneAuthProvider.OnVerificationStateChangedCallbacks() {
            override fun onVerificationCompleted(credential: PhoneAuthCredential) {
                trySend(PhoneVerificationState.VerificationCompleted(credential.smsCode))
            }

            override fun onVerificationFailed(e: FirebaseException) {
                trySend(PhoneVerificationState.VerificationFailed(e))
            }

            override fun onCodeSent(
                verificationId: String,
                token: PhoneAuthProvider.ForceResendingToken
            ) {
                trySend(PhoneVerificationState.CodeSent(verificationId, token))
            }

            override fun onCodeAutoRetrievalTimeOut(verificationId: String) {
                trySend(PhoneVerificationState.CodeAutoRetrievalTimeout(verificationId))
            }
        }

        val builder = PhoneAuthOptions.newBuilder(auth)
            .setPhoneNumber(phoneNumber)
            .setTimeout(timeoutSeconds, TimeUnit.SECONDS)
            .setActivity(activity)
            .setCallbacks(callbacks)

        if (resendToken is PhoneAuthProvider.ForceResendingToken) {
            builder.setForceResendingToken(resendToken)
        }

        PhoneAuthProvider.verifyPhoneNumber(builder.build())

        awaitClose { /* Cleanup if required */ }
    }
}
