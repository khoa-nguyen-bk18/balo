package com.devindie.balo.firebase.messaging.model

data class RemotePushMessage(
    val messageId: String? = null,
    val title: String? = null,
    val body: String? = null,
    val data: Map<String, String> = emptyMap()
)
