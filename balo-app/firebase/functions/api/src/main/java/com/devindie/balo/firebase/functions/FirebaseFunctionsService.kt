package com.devindie.balo.firebase.functions

interface FirebaseFunctionsService {
    suspend fun callFunction(name: String, data: Any? = null): Result<Any?>
    suspend fun <T> callTypedFunction(name: String, data: Any? = null, transform: (Any?) -> T): Result<T>
}
