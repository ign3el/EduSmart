package com.edustory.android.data.model

import com.google.gson.annotations.SerializedName

data class CheckDuplicateResponse(
    @SerializedName("is_duplicate") val isDuplicate: Boolean,
    @SerializedName("duplicate_type") val duplicateType: String?,
    @SerializedName("story_id") val existingStoryId: String?, // Backend sends 'story_id'
    @SerializedName("story_title") val existingStoryName: String?, // Backend sends 'story_title'
    @SerializedName("created_at") val createdAt: String?,
    @SerializedName("created_by") val createdBy: String?,
    @SerializedName("file_hash") val fileHash: String?
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
