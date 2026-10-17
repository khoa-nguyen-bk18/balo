package com.devindie.balo.firebase.auth.model

import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

class AuthUserTest {

    @Test
    fun `test auth user creation and properties`() {
        val user = AuthUser(
            uid = "test-uid-123",
            email = "test@example.com",
            displayName = "Test User",
            phoneNumber = "+1234567890",
            photoUrl = "https://example.com/avatar.png",
            isAnonymous = false,
            isEmailVerified = true
        )

        assertEquals("test-uid-123", user.uid)
        assertEquals("test@example.com", user.email)
        assertEquals("Test User", user.displayName)
        assertEquals("+1234567890", user.phoneNumber)
        assertEquals("https://example.com/avatar.png", user.photoUrl)
        assertTrue(user.isEmailVerified)
    }
}
