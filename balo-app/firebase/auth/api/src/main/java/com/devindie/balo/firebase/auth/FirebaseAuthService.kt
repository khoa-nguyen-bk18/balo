package com.devindie.balo.firebase.auth

import com.devindie.balo.firebase.auth.model.AuthUser
import kotlinx.coroutines.flow.Flow

interface FirebaseAuthService {
    val currentUser: AuthUser?
    val authState: Flow<AuthUser?>

    suspend fun signInWithEmailAndPassword(email: String, password: String): Result<AuthUser>
    suspend fun createUserWithEmailAndPassword(email: String, password: String): Result<AuthUser>
    suspend fun signInWithGoogle(idToken: String, accessToken: String? = null): Result<AuthUser>
    suspend fun signInWithPhoneCredential(verificationId: String, smsCode: String): Result<AuthUser>
    suspend fun sendPasswordResetEmail(email: String): Result<Unit>
    suspend fun signOut(): Result<Unit>
}
