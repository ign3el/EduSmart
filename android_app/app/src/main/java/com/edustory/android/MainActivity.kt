package com.edustory.android

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import com.edustory.android.ui.dashboard.StoryListScreen
import com.edustory.android.ui.login.LoginScreen
import com.edustory.android.ui.theme.EduStoryTheme

import com.edustory.android.ui.create.CreateStoryScreen
import com.edustory.android.ui.player.StoryPlayerScreen

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            EduStoryTheme {
                Surface(
                    modifier = Modifier.fillMaxSize(),
                    color = MaterialTheme.colorScheme.background
                ) {
                    var token by remember { mutableStateOf<String?>(null) }
                    var selectedStoryId by remember { mutableStateOf<String?>(null) }
                    var isCreatingStory by remember { mutableStateOf(false) }
                    
                    if (token == null) {
                        LoginScreen(onLoginSuccess = { newToken ->
                            token = newToken
                        })
                    } else if (isCreatingStory) {
                        CreateStoryScreen(
                            token = token!!,
                            onStoryCreated = { newStoryId ->
                                isCreatingStory = false
                                // Ideally refresh list or open new story
                                selectedStoryId = newStoryId
                            },
                            onBack = { isCreatingStory = false }
                        )
                    } else if (selectedStoryId != null) {
                        StoryPlayerScreen(
                            token = token!!,
                            storyId = selectedStoryId!!,
                            onBack = { selectedStoryId = null }
                        )
                    } else {
                        StoryListScreen(
                            token = token!!,
                            onStoryClick = { story ->
                                selectedStoryId = story.storyId
                            },
                            onFabClick = { isCreatingStory = true } // We need to add this to StoryListScreen too
                        )
                    }
                }
            }
        }
    }
}
