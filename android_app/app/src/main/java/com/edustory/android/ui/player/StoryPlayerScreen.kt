package com.edustory.android.ui.player

import android.media.AudioAttributes
import android.media.MediaPlayer
import android.util.Log
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.lifecycle.viewmodel.compose.viewModel
import coil.compose.AsyncImage
import coil.request.ImageRequest
import com.edustory.android.data.model.Scene
import com.edustory.android.network.RetrofitClient

@Composable
fun StoryPlayerScreen(
    token: String,
    storyId: String,
    onBack: () -> Unit,
    viewModel: StoryPlayerViewModel = viewModel()
) {
    val playerState by viewModel.playerState.collectAsState()
    val currentIndex by viewModel.currentSceneIndex.collectAsState()

    LaunchedEffect(storyId) {
        viewModel.loadStory(token, storyId)
    }

    Scaffold(
        topBar = {
            // Simple Top Bar
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(16.dp)
            ) {
                Button(onClick = onBack, modifier = Modifier.align(Alignment.CenterStart)) {
                    Text("Back")
                }
            }
        }
    ) { paddingValues ->
        Box(
            modifier = Modifier
                .fillMaxSize()
                .padding(paddingValues),
            contentAlignment = Alignment.Center
        ) {
            when (val state = playerState) {
                is PlayerState.Loading -> CircularProgressIndicator()
                is PlayerState.Error -> {
                    Column(horizontalAlignment = Alignment.CenterHorizontally) {
                        Text("Error: ${state.message}", color = Color.Red)
                        Button(onClick = { viewModel.loadStory(token, storyId) }) {
                            Text("Retry")
                        }
                    }
                }
                is PlayerState.Success -> {
                    val scenes = state.story.storyData.scenes
                    if (scenes.isNotEmpty()) {
                        SceneView(
                            scene = scenes[currentIndex],
                            currentIndex = currentIndex,
                            totalScenes = scenes.size,
                            onNext = { viewModel.nextScene(scenes.size) },
                            onPrev = { viewModel.prevScene() }
                        )
                    } else {
                        Text("This story has no scenes.")
                    }
                }
                is PlayerState.Idle -> Text("Initializing...")
            }
        }
    }
}

@Composable
fun SceneView(
    scene: Scene,
    currentIndex: Int,
    totalScenes: Int,
    onNext: () -> Unit,
    onPrev: () -> Unit
) {
    val context = LocalContext.current
    var isPlaying by remember { mutableStateOf(false) }
    var mediaPlayer by remember { mutableStateOf<MediaPlayer?>(null) }
    var audioError by remember { mutableStateOf<String?>(null) }

    // Audio Cleanup and Setup
    DisposableEffect(scene.audioUrl) {
        val player = MediaPlayer()
        mediaPlayer = player
        
        if (!scene.audioUrl.isNullOrEmpty()) {
            try {
                // Ensure URL is absolute. Since backend returns /api/... we need to prepend base URL if using RetrofitClient base
                // But RetrofitClient.BASE_URL is private. We hardcode or extract it.
                // Assuming backend returns relative path starting with /api/
                val fullAudioUrl = if (scene.audioUrl.startsWith("http")) scene.audioUrl else "https://edusmart.ign3el.com" + scene.audioUrl
                
                player.setAudioAttributes(
                    AudioAttributes.Builder()
                        .setContentType(AudioAttributes.CONTENT_TYPE_SPEECH)
                        .setUsage(AudioAttributes.USAGE_MEDIA)
                        .build()
                )
                player.setDataSource(fullAudioUrl)
                player.prepareAsync()
                player.setOnPreparedListener { 
                    // Ready to play
                    Log.d("StoryPlayer", "Audio prepared: $fullAudioUrl")
                }
                player.setOnCompletionListener {
                    isPlaying = false
                }
                player.setOnErrorListener { _, what, extra ->
                    Log.e("StoryPlayer", "Audio Error: $what, $extra")
                    audioError = "Audio Error"
                    isPlaying = false
                    true
                }
            } catch (e: Exception) {
                Log.e("StoryPlayer", "Audio Setup Failed", e)
                audioError = "Setup Failed"
            }
        }

        onDispose {
            try {
                if (player.isPlaying) {
                    player.stop()
                }
                player.release()
            } catch (e: Exception) {
                Log.e("StoryPlayer", "Release failed", e)
            }
        }
    }
    
    // Auto-stop when leaving scene
    DisposableEffect(Unit) {
        onDispose {
            mediaPlayer?.release()
        }
    }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(16.dp),
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        // Image
        Card(
            modifier = Modifier
                .weight(1f)
                .fillMaxWidth(),
            shape = RoundedCornerShape(16.dp),
            elevation = CardDefaults.cardElevation(8.dp)
        ) {
            if (!scene.imageUrl.isNullOrEmpty()) {
                val fullImageUrl = if (scene.imageUrl.startsWith("http")) scene.imageUrl else "https://edusmart.ign3el.com" + scene.imageUrl
                
                AsyncImage(
                    model = ImageRequest.Builder(context)
                        .data(fullImageUrl)
                        .crossfade(true)
                        .build(),
                    contentDescription = "Scene Image",
                    contentScale = ContentScale.Crop,
                    modifier = Modifier.fillMaxSize()
                )
            } else {
                Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                    Text("No Image")
                }
            }
        }

        Spacer(modifier = Modifier.height(16.dp))

        // Text
        Box(
            modifier = Modifier
                .weight(1f)
                .fillMaxWidth()
                .background(MaterialTheme.colorScheme.surfaceVariant, RoundedCornerShape(8.dp))
                .padding(16.dp)
        ) {
            Text(
                text = scene.text,
                style = MaterialTheme.typography.bodyLarge,
                textAlign = TextAlign.Start,
                modifier = Modifier.verticalScroll(rememberScrollState())
            )
        }

        Spacer(modifier = Modifier.height(16.dp))

        // Controls
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Button(onClick = onPrev, enabled = currentIndex > 0) {
                Text("Previous")
            }

            // Audio Control
            if (!scene.audioUrl.isNullOrEmpty()) {
                Button(
                    onClick = {
                        try {
                            if (isPlaying) {
                                mediaPlayer?.pause()
                                isPlaying = false
                            } else {
                                mediaPlayer?.start()
                                isPlaying = true
                            }
                        } catch (e: Exception) {
                            Log.e("StoryPlayer", "Play/Pause error", e)
                        }
                    },
                    colors = ButtonDefaults.buttonColors(
                        containerColor = if (isPlaying) MaterialTheme.colorScheme.primary else MaterialTheme.colorScheme.secondary
                    )
                ) {
                    Text(if (isPlaying) "Pause" else "Play Audio")
                }
            } else {
                Text("No Audio", style = MaterialTheme.typography.labelSmall)
            }

            Button(onClick = onNext, enabled = currentIndex < totalScenes - 1) {
                Text("Next")
            }
        }
        
        Spacer(modifier = Modifier.height(8.dp))
        Text(
            text = "Scene ${currentIndex + 1} of $totalScenes",
            style = MaterialTheme.typography.labelMedium
        )
    }
}
