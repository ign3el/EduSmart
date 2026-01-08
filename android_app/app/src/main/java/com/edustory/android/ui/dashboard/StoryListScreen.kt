package com.edustory.android.ui.dashboard

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.lifecycle.viewmodel.compose.viewModel
import com.edustory.android.data.model.Story
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

    Scaffold(
        floatingActionButton = {
            FloatingActionButton(onClick = onFabClick) {
                Text("+", style = MaterialTheme.typography.headlineMedium)
            }
        }
    ) { paddingValues ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(paddingValues)
                .padding(16.dp)
        ) {
        Text(
            text = "Your Stories",
            style = MaterialTheme.typography.headlineMedium,
            modifier = Modifier.padding(bottom = 16.dp)
        )

        when (val state = storyState) {
            is StoryState.Loading -> {
                Box(modifier = Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                    CircularProgressIndicator()
                }
            }
            is StoryState.Error -> {
                Box(modifier = Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                    Column(horizontalAlignment = Alignment.CenterHorizontally) {
                        Text(text = "Error: ${state.message}", color = MaterialTheme.colorScheme.error)
                        Button(onClick = { viewModel.fetchStories(token) }) {
                            Text("Retry")
                        }
                    }
                }
            }
            is StoryState.Success -> {
                if (state.stories.isEmpty()) {
                    Box(modifier = Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                        Text("No stories found. Create one on the web!")
                    }
                } else {
                    LazyColumn(
                        verticalArrangement = Arrangement.spacedBy(8.dp)
                    ) {
                        items(state.stories) { story ->
                            StoryCard(story = story, onClick = { onStoryClick(story) })
                        }
                    }
                }
            }
            is StoryState.Idle -> {
                // Do nothing
            }
        }
    }
}
}

@Composable
fun StoryCard(story: Story, onClick: () -> Unit) {
    Card(
        modifier = Modifier
            .fillMaxWidth()
            .clickable(onClick = onClick),
        elevation = CardDefaults.cardElevation(defaultElevation = 4.dp)
    ) {
        Column(
            modifier = Modifier
                .padding(16.dp)
        ) {
            Text(
                text = story.title,
                style = MaterialTheme.typography.titleMedium,
                fontWeight = FontWeight.Bold
            )
            Spacer(modifier = Modifier.height(4.dp))
            Text(
                text = "Saved: ${formatDate(story.savedAt)}",
                style = MaterialTheme.typography.bodySmall,
                color = Color.Gray
            )
        }
    }
}

fun formatDate(timestampStr: String): String {
    return try {
        // Backend usually sends timestamp in milliseconds or seconds
        // Adjust based on your actual backend format
        // Assuming string might be a date string or timestamp
        val sdf = SimpleDateFormat("MMM dd, yyyy", Locale.getDefault())
        // Simplification: just return simple string for now if parsing fails
        timestampStr
        // In real app, proper parsing is needed:
        // val date = Date(timestampStr.toLong())
        // sdf.format(date)
    } catch (e: Exception) {
        timestampStr
    }
}
