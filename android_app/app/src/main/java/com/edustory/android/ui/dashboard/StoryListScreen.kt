package com.edustory.android.ui.dashboard

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Add
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.lifecycle.viewmodel.compose.viewModel
import com.edustory.android.data.model.Story
import com.edustory.android.ui.components.GlassCard
import com.edustory.android.ui.components.GradientBackground
import com.edustory.android.ui.theme.*
import java.text.SimpleDateFormat
import java.util.*

@Composable
fun StoryListScreen(
    token: String,
    viewModel: StoryViewModel = viewModel(),
    onStoryClick: (Story) -> Unit,
    onFabClick: () -> Unit
) {
    val storyState by viewModel.storyState.collectAsState()

    // Fetch stories on first load
    LaunchedEffect(Unit) {
        viewModel.fetchStories(token)
    }

    GradientBackground {
        Scaffold(
            containerColor = androidx.compose.ui.graphics.Color.Transparent,
            floatingActionButton = {
                FloatingActionButton(
                    onClick = onFabClick,
                    containerColor = EduPrimary,
                    contentColor = androidx.compose.ui.graphics.Color.White
                ) {
                    Icon(Icons.Filled.Add, contentDescription = "Create Story")
                }
            }
        ) { paddingValues ->
            Column(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(paddingValues)
                    .padding(24.dp)
            ) {
                Text(
                    text = "📚 Your Stories",
                    style = MaterialTheme.typography.displaySmall,
                    fontWeight = FontWeight.Bold,
                    color = EduOnBackground,
                    modifier = Modifier.padding(bottom = 20.dp)
                )

                when (val state = storyState) {
                    is StoryState.Loading -> {
                        Box(modifier = Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                            CircularProgressIndicator(color = EduPrimary)
                        }
                    }
                    is StoryState.Error -> {
                        GlassCard(
                            modifier = Modifier.fillMaxWidth(),
                            borderColor = EduError
                        ) {
                            Column(horizontalAlignment = Alignment.CenterHorizontally) {
                                Text(
                                    text = "❌ Error: ${state.message}",
                                    color = EduError,
                                    style = MaterialTheme.typography.bodyMedium
                                )
                                Spacer(modifier = Modifier.height(12.dp))
                                Button(
                                    onClick = { viewModel.fetchStories(token) },
                                    colors = ButtonDefaults.buttonColors(containerColor = EduPrimary)
                                ) {
                                    Text("Retry")
                                }
                            }
                        }
                    }
                    is StoryState.Success -> {
                        if (state.stories.isEmpty()) {
                            Box(modifier = Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                                GlassCard(borderColor = EduTertiary) {
                                    Text(
                                        "No stories found. Create one!",
                                        color = EduOnSurface,
                                        style = MaterialTheme.typography.bodyLarge
                                    )
                                }
                            }
                        } else {
                            LazyColumn(
                                verticalArrangement = Arrangement.spacedBy(12.dp)
                            ) {
                                items(state.stories) { story ->
                                    StoryCard(story = story, onClick = { onStoryClick(story) })
                                }
                            }
                        }
                    }
                    is StoryState.Idle -> {}
                }
            }
        }
    }
}

@Composable
fun StoryCard(story: Story, onClick: () -> Unit) {
    GlassCard(
        modifier = Modifier.fillMaxWidth(),
        borderColor = AccentBlue,
        onClick = onClick
    ) {
        Column {
            Text(
                text = story.title,
                style = MaterialTheme.typography.titleLarge,
                fontWeight = FontWeight.Bold,
                color = EduOnBackground
            )
            Spacer(modifier = Modifier.height(6.dp))
            Text(
                text = "📅 Saved: ${formatDate(story.savedAt)}",
                style = MaterialTheme.typography.bodySmall,
                color = EduOnSurface
            )
        }
    }
}

fun formatDate(timestampStr: String): String {
    return try {
        timestampStr
    } catch (e: Exception) {
        timestampStr
    }
}
