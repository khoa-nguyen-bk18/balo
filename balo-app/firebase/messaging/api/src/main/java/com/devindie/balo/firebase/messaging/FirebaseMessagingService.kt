package com.devindie.balo.firebase.messaging

import com.devindie.balo.firebase.messaging.model.RemotePushMessage
import kotlinx.coroutines.flow.Flow

interface FirebaseMessagingService {
    suspend fun getToken(): Result<String>
    suspend fun deleteToken(): Result<Unit>
    suspend fun subscribeToTopic(topic: String): Result<Unit>
    suspend fun unsubscribeFromTopic(topic: String): Result<Unit>
    val incomingMessages: Flow<RemotePushMessage>
}
