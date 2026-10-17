package com.devindie.balo.firebase.functions

import com.google.firebase.functions.FirebaseFunctions
import kotlinx.coroutines.tasks.await

class DefaultFirebaseFunctionsService(
    private val functions: FirebaseFunctions = FirebaseFunctions.getInstance()
) : FirebaseFunctionsService {

    override suspend fun callFunction(name: String, data: Any?): Result<Any?> = runCatching {
        val callable = functions.getHttpsCallable(name)
        val result = if (data != null) {
            callable.call(data).await()
        } else {
            callable.call().await()
        }
        result.data
    }

    override suspend fun <T> callTypedFunction(
        name: String,
        data: Any?,
        transform: (Any?) -> T
    ): Result<T> = runCatching {
        val resultData = callFunction(name, data).getOrThrow()
        transform(resultData)
    }
}
