package com.devindie.balo.firebase.auth.model

data class AuthUser(
    val uid: String,
    val email: String? = null,
    val displayName: String? = null,
    val phoneNumber: String? = null,
    val photoUrl: String? = null,
    val isAnonymous: Boolean = false,
    val isEmailVerified: Boolean = false
)
