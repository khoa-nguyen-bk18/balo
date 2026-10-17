package com.devindie.balo.firebase.messaging

import com.devindie.balo.firebase.messaging.model.RemotePushMessage
import com.google.firebase.messaging.FirebaseMessaging
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.MutableSharedFlow
import kotlinx.coroutines.flow.asSharedFlow
import kotlinx.coroutines.tasks.await

class DefaultFirebaseMessagingService(
    private val messaging: FirebaseMessaging = FirebaseMessaging.getInstance()
) : FirebaseMessagingService {

    companion object {
        private val _incomingMessages = MutableSharedFlow<RemotePushMessage>(extraBufferCapacity = 64)
        val sharedIncomingMessages: Flow<RemotePushMessage> = _incomingMessages.asSharedFlow()

        internal fun dispatchMessage(message: RemotePushMessage) {
            _incomingMessages.tryEmit(message)
        }
    }

    override val incomingMessages: Flow<RemotePushMessage> = sharedIncomingMessages

    override suspend fun getToken(): Result<String> = runCatching {
        messaging.token.await()
    }

    override suspend fun deleteToken(): Result<Unit> = runCatching {
        messaging.deleteToken().await()
    }

    override suspend fun subscribeToTopic(topic: String): Result<Unit> = runCatching {
        messaging.subscribeToTopic(topic).await()
    }

    override suspend fun unsubscribeFromTopic(topic: String): Result<Unit> = runCatching {
        messaging.unsubscribeFromTopic(topic).await()
    }
}
