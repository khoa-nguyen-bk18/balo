package com.devindie.balo.firebase.firestore

import com.google.firebase.firestore.FirebaseFirestore
import com.google.firebase.firestore.SetOptions
import kotlinx.coroutines.channels.awaitClose
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.callbackFlow
import kotlinx.coroutines.tasks.await

class DefaultFirebaseFirestoreService(
    private val firestore: FirebaseFirestore = FirebaseFirestore.getInstance()
) : FirebaseFirestoreService {

    override suspend fun getDocument(
        collection: String,
        documentId: String
    ): Result<Map<String, Any?>?> = runCatching {
        val snapshot = firestore.collection(collection).document(documentId).get().await()
        if (snapshot.exists()) snapshot.data else null
    }

    override suspend fun setDocument(
        collection: String,
        documentId: String,
        data: Map<String, Any?>,
        merge: Boolean
    ): Result<Unit> = runCatching {
        val docRef = firestore.collection(collection).document(documentId)
        if (merge) {
            docRef.set(data, SetOptions.merge()).await()
        } else {
            docRef.set(data).await()
        }
        Unit
    }

    override suspend fun updateDocument(
        collection: String,
        documentId: String,
        data: Map<String, Any?>
    ): Result<Unit> = runCatching {
        firestore.collection(collection).document(documentId).update(data).await()
        Unit
    }

    override suspend fun deleteDocument(
        collection: String,
        documentId: String
    ): Result<Unit> = runCatching {
        firestore.collection(collection).document(documentId).delete().await()
        Unit
    }

    override suspend fun getCollection(
        collection: String
    ): Result<List<Map<String, Any?>>> = runCatching {
        val snapshot = firestore.collection(collection).get().await()
        snapshot.documents.mapNotNull { it.data }
    }

    override fun observeDocument(
        collection: String,
        documentId: String
    ): Flow<Map<String, Any?>?> = callbackFlow {
        val listener = firestore.collection(collection).document(documentId)
            .addSnapshotListener { snapshot, error ->
                if (error != null) {
                    close(error)
                    return@addSnapshotListener
                }
                trySend(if (snapshot?.exists() == true) snapshot.data else null)
            }
        awaitClose {
            listener.remove()
        }
    }

    override fun observeCollection(
        collection: String
    ): Flow<List<Map<String, Any?>>> = callbackFlow {
        val listener = firestore.collection(collection)
            .addSnapshotListener { snapshot, error ->
                if (error != null) {
                    close(error)
                    return@addSnapshotListener
                }
                val items = snapshot?.documents?.mapNotNull { it.data } ?: emptyList()
                trySend(items)
            }
        awaitClose {
            listener.remove()
        }
    }
}
