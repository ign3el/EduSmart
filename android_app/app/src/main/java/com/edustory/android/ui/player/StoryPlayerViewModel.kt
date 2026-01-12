package com.edustory.android.ui.player

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.edustory.android.data.model.StoryDetailResponse
import com.edustory.android.data.model.Scene
import com.edustory.android.network.RetrofitClient
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import retrofit2.Call
import retrofit2.Callback
import retrofit2.Response

sealed class PlayerState {
    object Idle : PlayerState()
    object Loading : PlayerState()
    data class Success(val story: StoryDetailResponse) : PlayerState()
    data class Error(val message: String) : PlayerState()
}

class StoryPlayerViewModel : ViewModel() {

    private val _playerState = MutableStateFlow<PlayerState>(PlayerState.Idle)
    val playerState: StateFlow<PlayerState> = _playerState.asStateFlow()

    private val _currentSceneIndex = MutableStateFlow(0)
    val currentSceneIndex: StateFlow<Int> = _currentSceneIndex.asStateFlow()

    private val _ttsReadyScenes = MutableStateFlow<List<Int>>(emptyList())
    val ttsReadyScenes: StateFlow<List<Int>> = _ttsReadyScenes.asStateFlow()

    private val _ttsPolling = MutableStateFlow(false)
    val ttsPolling: StateFlow<Boolean> = _ttsPolling.asStateFlow()

    fun loadStory(token: String, storyId: String) {
        _playerState.value = PlayerState.Loading
        
        val authToken = if (token.startsWith("Bearer ")) token else "Bearer $token"
        
        RetrofitClient.instance.loadStory(storyId, authToken).enqueue(object : Callback<StoryDetailResponse> {
            override fun onResponse(call: Call<StoryDetailResponse>, response: Response<StoryDetailResponse>) {
                if (response.isSuccessful && response.body() != null) {
                    _playerState.value = PlayerState.Success(response.body()!!)
                    _currentSceneIndex.value = 0
                    // Start TTS polling for active stories
                    startTtsPolling(token, storyId)
                } else {
                    _playerState.value = PlayerState.Error("Failed to load story: ${response.code()}")
                }
            }

            override fun onFailure(call: Call<StoryDetailResponse>, t: Throwable) {
                _playerState.value = PlayerState.Error(t.message ?: "Unknown network error")
            }
        })
    }

    fun startTtsPolling(token: String, storyId: String) {
        if (_ttsPolling.value) return // Already polling
        
        _ttsPolling.value = true
        val authToken = if (token.startsWith("Bearer ")) token else "Bearer $token"
        
        viewModelScope.launch {
            while (_ttsPolling.value) {
                try {
                    val response = RetrofitClient.instance.getTtsStatus(storyId, authToken).execute()
                    if (response.isSuccessful && response.body() != null) {
                        val status = response.body()!!
                        _ttsReadyScenes.value = status.scenes_ready
                        
                        // Stop polling when complete
                        if (status.is_complete) {
                            _ttsPolling.value = false
                        }
                    }
                } catch (e: Exception) {
                    // Silently continue polling on error
                }
                
                // Poll every 3 seconds
                kotlinx.coroutines.delay(3000)
            }
        }
    }

    fun stopTtsPolling() {
        _ttsPolling.value = false
    }

    fun nextScene(totalScenes: Int) {
        if (_currentSceneIndex.value < totalScenes - 1) {
            _currentSceneIndex.value += 1
        }
    }

    fun prevScene() {
        if (_currentSceneIndex.value > 0) {
            _currentSceneIndex.value -= 1
        }
    }

    override fun onCleared() {
        super.onCleared()
        stopTtsPolling()
    }
}
