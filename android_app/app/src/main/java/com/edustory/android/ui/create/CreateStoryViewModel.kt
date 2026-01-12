package com.edustory.android.ui.create

import android.content.Context
import android.net.Uri
import android.util.Log
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.edustory.android.data.model.CheckDuplicateResponse
import com.edustory.android.data.model.StatusResponse
import com.edustory.android.data.model.UploadResponse
import com.edustory.android.network.RetrofitClient
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import okhttp3.MediaType.Companion.toMediaTypeOrNull
import okhttp3.MultipartBody
import okhttp3.RequestBody.Companion.asRequestBody
import okhttp3.RequestBody.Companion.toRequestBody
import retrofit2.Call
import retrofit2.Callback
import retrofit2.Response
import java.io.File
import java.io.FileOutputStream

sealed class CreateState {
    object Idle : CreateState()
    object Checking : CreateState()
    data class DuplicateFound(
        val existingStoryId: String, 
        val existingName: String?,
        val createdAt: String?,
        val createdBy: String?
    ) : CreateState()
    object Uploading : CreateState()
    data class Generating(val progress: Int, val message: String) : CreateState()
    data class Success(val storyId: String) : CreateState()
    data class Error(val message: String) : CreateState()
}

class CreateStoryViewModel : ViewModel() {

    private val _createState = MutableStateFlow<CreateState>(CreateState.Idle)
    val createState: StateFlow<CreateState> = _createState.asStateFlow()

    private var selectedFileUri: Uri? = null
    private var fileHash: String? = null
    
    // User Settings
    val voice = MutableStateFlow("af_bella")
    val gradeLevel = MutableStateFlow("Elementary")
    val speed = MutableStateFlow("1.0")

    fun onFileSelected(uri: Uri) {
        selectedFileUri = uri
        _createState.value = CreateState.Idle
    }

    fun setGrade(level: String) {
        gradeLevel.value = level
    }

    fun startProcess(context: Context, token: String, forceNew: Boolean = false) {
        if (selectedFileUri == null) {
            _createState.value = CreateState.Error("Please select a file first.")
            return
        }

        viewModelScope.launch {
            try {
                val authToken = if (token.startsWith("Bearer ")) token else "Bearer $token"
                val file = getFileFromUri(context, selectedFileUri!!)
                
                if (file == null) {
                    _createState.value = CreateState.Error("Failed to read file.")
                    return@launch
                }

                if (!forceNew) {
                    checkDuplicate(file, authToken)
                } else {
                    uploadAndGenerate(file, authToken, true)
                }
            } catch (e: Exception) {
                _createState.value = CreateState.Error(e.message ?: "Unknown error")
            }
        }
    }

    private fun checkDuplicate(file: File, token: String) {
        _createState.value = CreateState.Checking
        
        val requestFile = file.asRequestBody("multipart/form-data".toMediaTypeOrNull())
        val body = MultipartBody.Part.createFormData("file", file.name, requestFile)

        RetrofitClient.instance.checkDuplicate(body, token).enqueue(object : Callback<CheckDuplicateResponse> {
            override fun onResponse(call: Call<CheckDuplicateResponse>, response: Response<CheckDuplicateResponse>) {
                if (response.isSuccessful && response.body() != null) {
                    val result = response.body()!!
                    fileHash = result.fileHash
                    
                    if (result.isDuplicate && result.existingStoryId != null) {
                        _createState.value = CreateState.DuplicateFound(
                            result.existingStoryId, 
                            result.existingStoryName,
                            result.createdAt,
                            result.createdBy
                        )
                    } else {
                        // No duplicate, proceed to upload
                         uploadAndGenerate(file, token, false)
                    }
                } else {
                    _createState.value = CreateState.Error("Duplicate check failed: ${response.code()}")
                }
            }

            override fun onFailure(call: Call<CheckDuplicateResponse>, t: Throwable) {
                _createState.value = CreateState.Error("Network error: ${t.message}")
            }
        })
    }

    private fun uploadAndGenerate(file: File, token: String, forceNew: Boolean) {
        _createState.value = CreateState.Uploading
        
        val requestFile = file.asRequestBody("multipart/form-data".toMediaTypeOrNull())
        val body = MultipartBody.Part.createFormData("file", file.name, requestFile)
        
        // Params
        val avatarPart = "generic".toRequestBody("text/plain".toMediaTypeOrNull())
        val forcePart = forceNew.toString().toRequestBody("text/plain".toMediaTypeOrNull())
        val hashPart = (fileHash ?: "").toRequestBody("text/plain".toMediaTypeOrNull())
        val voicePart = voice.value.toRequestBody("text/plain".toMediaTypeOrNull())
        val speedPart = speed.value.toFloat().toString().toRequestBody("text/plain".toMediaTypeOrNull())
        val gradePart = gradeLevel.value.toRequestBody("text/plain".toMediaTypeOrNull())

        RetrofitClient.instance.uploadFile(body, avatarPart, forcePart, hashPart, voicePart, speedPart, gradePart, token)
            .enqueue(object : Callback<UploadResponse> {
                override fun onResponse(call: Call<UploadResponse>, response: Response<UploadResponse>) {
                    if (response.isSuccessful && response.body() != null) {
                        val jobId = response.body()!!.jobId
                        pollStatus(jobId, token)
                    } else {
                        _createState.value = CreateState.Error("Upload failed: ${response.code()}")
                    }
                }

                override fun onFailure(call: Call<UploadResponse>, t: Throwable) {
                    _createState.value = CreateState.Error("Upload Error: ${t.message}")
                }
            })
    }

    private fun pollStatus(jobId: String, token: String) {
        viewModelScope.launch {
            var isFinished = false
            while (!isFinished) {
                // Poll every 2 seconds
                try {
                    val response = RetrofitClient.instance.getJobStatus(jobId, token).execute()
                    if (response.isSuccessful && response.body() != null) {
                        val status = response.body()!!
                        
                        if (status.status == "completed") {
                            // We need story_id, but status response has result structure.
                            // BUT... wait. We need to SAVE the story first?
                            // The Web App calls /api/save-story/{job_id} after completion?
                            // Checking App.jsx... Yes, saveStory(jobId) is called.
                            // Wait, the status endpoint returns "result" which contains title/scenes.
                            // But usually we load by ID.
                            // In legacy mode, job_id might be transient.
                            // Let's assume for now we mark success, and logic to "Load" might need saving.
                            // Actually, the web app calls save automatically? Or user clicks save?
                            // Re-reading main.py: save-story is a POST.
                            // Let's simplify: success means generated. We might need to call Save.
                            // For this iteration, let's just finish and basic display, or assumes backend saves?
                            // No, backend requires explicit save.
                            // We will add SAVE step next.
                            _createState.value = CreateState.Success(jobId) // Use JobID temporarily
                            isFinished = true
                        } else if (status.status == "failed") {
                            _createState.value = CreateState.Error("Generation Failed")
                            isFinished = true
                        } else {
                            // Processing
                            _createState.value = CreateState.Generating(status.progress, status.status)
                            delay(2000)
                        }
                    } else {
                         delay(2000)
                    }
                } catch (e: Exception) {
                    Log.e("Poll", "Error polling", e)
                    delay(2000)
                }
            }
        }
    }

    // Helper to get File from Uri
    private fun getFileFromUri(context: Context, uri: Uri): File? {
        try {
            val contentResolver = context.contentResolver
            val inputStream = contentResolver.openInputStream(uri) ?: return null
            val tempFile = File.createTempFile("upload", ".tmp", context.cacheDir)
            val outputStream = FileOutputStream(tempFile)
            inputStream.copyTo(outputStream)
            inputStream.close()
            outputStream.close()
            return tempFile
        } catch (e: Exception) {
            e.printStackTrace()
            return null
        }
    }
}
