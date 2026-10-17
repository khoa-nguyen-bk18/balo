package com.devindie.balo.firebase.messaging

import com.devindie.balo.firebase.messaging.model.RemotePushMessage
import com.google.firebase.messaging.FirebaseMessagingService
import com.google.firebase.messaging.RemoteMessage

class BaloFirebaseMessagingReceiverService : FirebaseMessagingService() {

    override fun onMessageReceived(remoteMessage: RemoteMessage) {
        super.onMessageReceived(remoteMessage)

        val pushMessage = RemotePushMessage(
            messageId = remoteMessage.messageId,
            title = remoteMessage.notification?.title,
            body = remoteMessage.notification?.body,
            data = remoteMessage.data
        )

        DefaultFirebaseMessagingService.dispatchMessage(pushMessage)
    }

    override fun onNewToken(token: String) {
        super.onNewToken(token)
        // Token refreshed - applications can observe or handle token updates
    }
}
