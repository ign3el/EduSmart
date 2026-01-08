package com.edustory.android.network

import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory

object RetrofitClient {
    // Production VPS URL
    private const val BASE_URL = "https://edusmart.ign3el.com/"

    val instance: AuthApiService by lazy {
        val retrofit = Retrofit.Builder()
            .baseUrl(BASE_URL)
            .addConverterFactory(GsonConverterFactory.create())
            .build()

        retrofit.create(AuthApiService::class.java)
    }
}
