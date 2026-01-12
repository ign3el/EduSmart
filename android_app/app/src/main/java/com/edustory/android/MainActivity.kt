package com.edustory.android

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import com.edustory.android.ui.create.CreateStoryScreen
import com.edustory.android.ui.dashboard.StoryListScreen
import com.edustory.android.ui.home.HomeScreen
import com.edustory.android.ui.login.LoginScreen
import com.edustory.android.ui.offline.OfflineLibraryScreen
import com.edustory.android.ui.player.StoryPlayerScreen
import com.edustory.android.ui.theme.EduStoryTheme

class MainActivity : ComponentActivity() {
    @OptIn(ExperimentalMaterial3Api::class)
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            EduStoryTheme {
                Surface(
                    modifier = Modifier.fillMaxSize(),
                    color = MaterialTheme.colorScheme.background
                ) {
                    var token by remember { mutableStateOf<String?>(null) }
                    var currentScreen by remember { mutableStateOf("home") } // home, create, library, offline, player
                    var selectedStoryId by remember { mutableStateOf<String?>(null) }
                    
                    if (token == null) {
                        LoginScreen(onLoginSuccess = { newToken ->
                            token = newToken
                            currentScreen = "home"
                        })
                    } else {
                        when (currentScreen) {
                            "home" -> HomeScreen(
                                onNavigateToCreate = { currentScreen = "create" },
                                onNavigateToLibrary = { currentScreen = "library" },
                                onNavigateToOffline = { currentScreen = "offline" }
                            )
                            "create" -> CreateStoryScreen(
                                token = token!!,
                                onStoryCreated = { newStoryId ->
                                    selectedStoryId = newStoryId
                                    currentScreen = "player"
                                },
                                onBack = { currentScreen = "home" }
                            )
                            "library" -> StoryListScreen(
                                token = token!!,
                                onStoryClick = { story ->
                                    selectedStoryId = story.storyId
                                    currentScreen = "player"
                                },
                                onFabClick = { currentScreen = "create" }
                            )
                            "offline" -> OfflineLibraryScreen(
                                onBack = { currentScreen = "home" }
                            )
                            "player" -> {
                                if (selectedStoryId != null) {
                                    StoryPlayerScreen(
                                        token = token!!,
                                        storyId = selectedStoryId!!,
                                        onBack = { 
                                            currentScreen = "home" 
                                            selectedStoryId = null
                                        }
                                    )
                                } else {
                                    currentScreen = "home"
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}
