package com.devindie.balo.firebase.firestore

import kotlinx.coroutines.flow.Flow

interface FirebaseFirestoreService {
    suspend fun getDocument(collection: String, documentId: String): Result<Map<String, Any?>?>
    suspend fun setDocument(
        collection: String,
        documentId: String,
        data: Map<String, Any?>,
        merge: Boolean = false
    ): Result<Unit>
    suspend fun updateDocument(
        collection: String,
        documentId: String,
        data: Map<String, Any?>
    ): Result<Unit>
    suspend fun deleteDocument(collection: String, documentId: String): Result<Unit>
    suspend fun getCollection(collection: String): Result<List<Map<String, Any?>>>
    fun observeDocument(collection: String, documentId: String): Flow<Map<String, Any?>?>
    fun observeCollection(collection: String): Flow<List<Map<String, Any?>>>
}
