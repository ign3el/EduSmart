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

    fun loadStory(token: String, storyId: String) {
        _playerState.value = PlayerState.Loading
        
        val authToken = if (token.startsWith("Bearer ")) token else "Bearer $token"
        
        RetrofitClient.instance.loadStory(storyId, authToken).enqueue(object : Callback<StoryDetailResponse> {
            override fun onResponse(call: Call<StoryDetailResponse>, response: Response<StoryDetailResponse>) {
                if (response.isSuccessful && response.body() != null) {
                    _playerState.value = PlayerState.Success(response.body()!!)
                    _currentSceneIndex.value = 0
                } else {
                    _playerState.value = PlayerState.Error("Failed to load story: ${response.code()}")
                }
            }

            override fun onFailure(call: Call<StoryDetailResponse>, t: Throwable) {
                _playerState.value = PlayerState.Error(t.message ?: "Unknown network error")
            }
        })
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
}
