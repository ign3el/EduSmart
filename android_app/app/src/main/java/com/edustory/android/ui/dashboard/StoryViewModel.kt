package com.edustory.android.ui.dashboard

import androidx.lifecycle.ViewModel
import com.edustory.android.data.model.Story
import com.edustory.android.network.RetrofitClient
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import retrofit2.Call
import retrofit2.Callback
import retrofit2.Response

class StoryViewModel : ViewModel() {

    private val _storyState = MutableStateFlow<StoryState>(StoryState.Idle)
    val storyState: StateFlow<StoryState> = _storyState.asStateFlow()

    fun fetchStories(token: String) {
        _storyState.value = StoryState.Loading
        
        // Add Bearer prefix if not present
        val authToken = if (token.startsWith("Bearer ")) token else "Bearer $token"

        val call = RetrofitClient.instance.listStories(authToken)
        call.enqueue(object : Callback<List<Story>> {
            override fun onResponse(call: Call<List<Story>>, response: Response<List<Story>>) {
                if (response.isSuccessful) {
                    val stories = response.body() ?: emptyList()
                    _storyState.value = StoryState.Success(stories)
                } else {
                    _storyState.value = StoryState.Error("Failed to load stories: ${response.code()}")
                }
            }

            override fun onFailure(call: Call<List<Story>>, t: Throwable) {
                _storyState.value = StoryState.Error(t.message ?: "Unknown error")
            }
        })
    }
}

sealed class StoryState {
    object Idle : StoryState()
    object Loading : StoryState()
    data class Success(val stories: List<Story>) : StoryState()
    data class Error(val message: String) : StoryState()
}
