package com.devindie.balo.firebase.auth

import com.devindie.balo.firebase.auth.model.AuthUser
import com.google.firebase.auth.FirebaseAuth
import com.google.firebase.auth.FirebaseUser
import com.google.firebase.auth.GoogleAuthProvider
import com.google.firebase.auth.PhoneAuthProvider
import kotlinx.coroutines.channels.awaitClose
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.callbackFlow
import kotlinx.coroutines.tasks.await

class DefaultFirebaseAuthService(
    private val auth: FirebaseAuth = FirebaseAuth.getInstance()
) : FirebaseAuthService {

    override val currentUser: AuthUser?
        get() = auth.currentUser?.toAuthUser()

    override val authState: Flow<AuthUser?> = callbackFlow {
        val listener = FirebaseAuth.AuthStateListener { firebaseAuth ->
            trySend(firebaseAuth.currentUser?.toAuthUser())
        }
        auth.addAuthStateListener(listener)
        awaitClose {
            auth.removeAuthStateListener(listener)
        }
    }

    override suspend fun signInWithEmailAndPassword(
        email: String,
        password: String
    ): Result<AuthUser> = runCatching {
        val result = auth.signInWithEmailAndPassword(email, password).await()
        val user = result.user?.toAuthUser()
            ?: throw IllegalStateException("FirebaseUser is null after successful email sign-in")
        user
    }

    override suspend fun createUserWithEmailAndPassword(
        email: String,
        password: String
    ): Result<AuthUser> = runCatching {
        val result = auth.createUserWithEmailAndPassword(email, password).await()
        val user = result.user?.toAuthUser()
            ?: throw IllegalStateException("FirebaseUser is null after successful account creation")
        user
    }

    override suspend fun signInWithGoogle(
        idToken: String,
        accessToken: String?
    ): Result<AuthUser> = runCatching {
        val credential = GoogleAuthProvider.getCredential(idToken, accessToken)
        val result = auth.signInWithCredential(credential).await()
        val user = result.user?.toAuthUser()
            ?: throw IllegalStateException("FirebaseUser is null after Google sign-in")
        user
    }

    override suspend fun signInWithPhoneCredential(
        verificationId: String,
        smsCode: String
    ): Result<AuthUser> = runCatching {
        val credential = PhoneAuthProvider.getCredential(verificationId, smsCode)
        val result = auth.signInWithCredential(credential).await()
        val user = result.user?.toAuthUser()
            ?: throw IllegalStateException("FirebaseUser is null after phone credential sign-in")
        user
    }

    override suspend fun sendPasswordResetEmail(email: String): Result<Unit> = runCatching {
        auth.sendPasswordResetEmail(email).await()
    }

    override suspend fun signOut(): Result<Unit> = runCatching {
        auth.signOut()
    }

    private fun FirebaseUser.toAuthUser(): AuthUser = AuthUser(
        uid = uid,
        email = email,
        displayName = displayName,
        phoneNumber = phoneNumber,
        photoUrl = photoUrl?.toString(),
        isAnonymous = isAnonymous,
        isEmailVerified = isEmailVerified
    )
}
