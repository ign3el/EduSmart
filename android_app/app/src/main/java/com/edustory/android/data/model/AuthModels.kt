package com.edustory.android.data.model

import com.google.gson.annotations.SerializedName

data class TokenResponse(
    @SerializedName("access_token") val accessToken: String,
    @SerializedName("token_type") val tokenType: String
)

data class User(
    val id: Int,
    val email: String,
    val username: String,
    @SerializedName("is_verified") val isVerified: Boolean,
    @SerializedName("is_premium") val isPremium: Boolean,
    @SerializedName("is_admin") val isAdmin: Boolean
)

data class Story(
    @SerializedName("story_id") val storyId: String,
    @SerializedName("name") val title: String, // Mapping 'name' to 'title' for clarity
    @SerializedName("saved_at") val savedAt: String
)

data class StoryDetailResponse(
    val name: String,
    @SerializedName("story_data") val storyData: StoryData
)

data class StoryData(
    val title: String?,
    val scenes: List<Scene>,
    val quiz: List<QuizItem>?
)

data class Scene(
    val text: String,
    @SerializedName("image_url") val imageUrl: String?,
    @SerializedName("audio_url") val audioUrl: String?
)

data class QuizItem(
    val question: String,
    val options: List<String>,
    @SerializedName("correct_answer") val correctAnswer: String
)
