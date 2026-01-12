package com.edustory.android.network

import com.edustory.android.data.model.TokenResponse
import com.edustory.android.data.model.User
import com.edustory.android.data.model.Story
import com.edustory.android.data.model.StoryDetailResponse
import com.edustory.android.data.model.CheckDuplicateResponse
import com.edustory.android.data.model.UploadResponse
import com.edustory.android.data.model.StatusResponse
import okhttp3.MultipartBody
import okhttp3.RequestBody
import retrofit2.Call
import retrofit2.http.GET
import retrofit2.http.POST
import retrofit2.http.Multipart
import retrofit2.http.Part
import retrofit2.http.Header
import retrofit2.http.Path
import okhttp3.ResponseBody
import retrofit2.http.Field
import retrofit2.http.FormUrlEncoded

interface AuthApiService {

    @FormUrlEncoded
    @POST("/api/auth/token")
    fun login(
        @Field("username") username: String,
        @Field("password") password: String,
        @Field("grant_type") grantType: String = "password"
    ): Call<TokenResponse>

    @GET("/api/auth/me")
    fun getCurrentUser(
        @Header("Authorization") token: String
    ): Call<User>

    @GET("/api/list-stories")
    fun listStories(
        @Header("Authorization") token: String
    ): Call<List<Story>>

    @GET("/api/load-story/{storyId}")
    fun loadStory(
        @Path("storyId") storyId: String,
        @Header("Authorization") token: String
    ): Call<StoryDetailResponse>

    @Multipart
    @POST("/api/check-duplicate")
    fun checkDuplicate(
        @Part file: MultipartBody.Part,
        @Header("Authorization") token: String
    ): Call<CheckDuplicateResponse>

    @Multipart
    @POST("/api/upload")
    fun uploadFile(
        @Part file: MultipartBody.Part,
        @Part("avatar") avatar: RequestBody,
        @Part("force_new") forceNew: RequestBody,
        @Part("file_hash") fileHash: RequestBody?,
        @Part("voice") voice: RequestBody,
        @Part("speed") speed: RequestBody,
        @Part("grade_level") gradeLevel: RequestBody,
        @Header("Authorization") token: String
    ): Call<UploadResponse>

    @GET("/api/status/{jobId}")
    fun getJobStatus(
        @Path("jobId") jobId: String,
        @Header("Authorization") token: String
    ): Call<StatusResponse>

    @GET("/api/story/{storyId}/tts-status")
    fun getTtsStatus(
        @Path("storyId") storyId: String,
        @Header("Authorization") token: String
    ): Call<TtsStatusResponse>
}

// TTS Status Response Data Class
data class TtsStatusResponse(
    val tts_progress: String,
    val scenes_ready: List<Int>,
    val percentage: Int,
    val is_complete: Boolean
)
