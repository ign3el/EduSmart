package com.edustory.android.ui.player

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
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.lifecycle.viewmodel.compose.viewModel
import androidx.media3.common.MediaItem
import androidx.media3.common.Player
import androidx.media3.exoplayer.ExoPlayer
import coil.compose.AsyncImage
import coil.request.ImageRequest
import com.edustory.android.data.model.Scene
import com.edustory.android.network.RetrofitClient
import com.edustory.android.ui.components.GradientBackground
import com.edustory.android.ui.theme.*

@Composable
fun StoryPlayerScreen(
    token: String,
    storyId: String,
    onBack: () -> Unit,
    viewModel: StoryPlayerViewModel = viewModel()
) {
    val playerState by viewModel.playerState.collectAsState()
    val currentIndex by viewModel.currentSceneIndex.collectAsState()

    val ttsReadyScenes by viewModel.ttsReadyScenes.collectAsState()

    LaunchedEffect(storyId) {
        viewModel.loadStory(token, storyId)
    }

    Scaffold(
        topBar = {
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
                            storyId = storyId,
                            currentIndex = currentIndex,
                            totalScenes = scenes.size,
                            ttsReadyScenes = ttsReadyScenes,
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
    storyId: String,
    currentIndex: Int,
    totalScenes: Int,
    ttsReadyScenes: List<Int>,
    onNext: () -> Unit,
    onPrev: () -> Unit
) {
    val context = LocalContext.current
    var isPlaying by remember { mutableStateOf(false) }
    var exoPlayer by remember { mutableStateOf<ExoPlayer?>(null) }
    
    // Determine effective Audio URL
    // If scene index is in ttsReadyScenes, use the direct progressive endpoint
    val effectiveAudioUrl = remember(scene.audioUrl, ttsReadyScenes, currentIndex) {
        if (ttsReadyScenes.contains(currentIndex)) {
            "https://edusmart.ign3el.com/api/story/$storyId/scene/$currentIndex/audio"
        } else if (!scene.audioUrl.isNullOrEmpty()) {
            if (scene.audioUrl.startsWith("http")) scene.audioUrl else "https://edusmart.ign3el.com${scene.audioUrl}"
        } else {
            null
        }
    }

    // Initialize ExoPlayer
    LaunchedEffect(effectiveAudioUrl) {
        // Release previous player if it exists (though usually handled by onDispose)
        exoPlayer?.release()
        
        if (!effectiveAudioUrl.isNullOrEmpty()) {
            val player = ExoPlayer.Builder(context).build()
            exoPlayer = player
            
            Log.d("ExoPlayer", "Loading: $effectiveAudioUrl")

            try {
                val mediaItem = MediaItem.fromUri(fullAudioUrl)
                player.setMediaItem(mediaItem)
                player.prepare()
                player.playWhenReady = false // Don't auto-play immediately, let user control
                
                player.addListener(object : Player.Listener {
                    override fun onIsPlayingChanged(playing: Boolean) {
                        isPlaying = playing
                    }
                    
                    override fun onPlaybackStateChanged(playbackState: Int) {
                        if (playbackState == Player.STATE_ENDED) {
                            isPlaying = false
                            player.seekTo(0)
                            player.pause()
                        }
                    }
                    
                    override fun onPlayerError(error: androidx.media3.common.PlaybackException) {
                        Log.e("ExoPlayer", "Error: ${error.message}")
                        isPlaying = false
                    }
                })
            } catch (e: Exception) {
                Log.e("ExoPlayer", "Setup Failed", e)
            }
        } else {
            exoPlayer = null
        }
    }

    // Cleanup on Dispose
    DisposableEffect(Unit) {
        onDispose {
            exoPlayer?.release()
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
                val fullImageUrl = if (scene.imageUrl.startsWith("http")) 
                    scene.imageUrl 
                else 
                    "https://edusmart.ign3el.com" + scene.imageUrl
                
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
                        exoPlayer?.let { player ->
                            if (isPlaying) {
                                player.pause()
                            } else {
                                player.play()
                            }
                        }
                    },
                    colors = ButtonDefaults.buttonColors(
                        containerColor = if (isPlaying) MaterialTheme.colorScheme.primary else MaterialTheme.colorScheme.secondary
                    )
                ) {
                    Text(if (isPlaying) "Pause" else "Play Audio")
                }
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
