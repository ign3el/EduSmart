package com.edustory.android.data.model

import com.google.gson.annotations.SerializedName

data class CheckDuplicateResponse(
    @SerializedName("is_duplicate") val isDuplicate: Boolean,
    @SerializedName("file_hash") val fileHash: String,
    @SerializedName("existing_story_id") val existingStoryId: String?,
    @SerializedName("existing_story_name") val existingStoryName: String?
)

data class UploadResponse(
    @SerializedName("job_id") val jobId: String,
    val message: String
)

data class StatusResponse(
    val status: String,
    val progress: Int,
    @SerializedName("total_scenes") val totalScenes: Int,
    @SerializedName("completed_scene_count") val completedSceneCount: Int,
    val result: StoryData? // Reusing StoryData from AuthModels.kt
)
