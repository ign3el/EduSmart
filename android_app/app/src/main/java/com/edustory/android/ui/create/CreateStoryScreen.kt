package com.edustory.android.ui.create

import android.net.Uri
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.layout.*
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Add
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.lifecycle.viewmodel.compose.viewModel

@Composable
fun CreateStoryScreen(
    token: String,
    onStoryCreated: (String) -> Unit, // Callback with Story ID (or Job ID)
    onBack: () -> Unit,
    viewModel: CreateStoryViewModel = viewModel()
) {
    val context = LocalContext.current
    val createState by viewModel.createState.collectAsState()
    val voice by viewModel.voice.collectAsState()
    val grade by viewModel.gradeLevel.collectAsState()
    
    var fileName by remember { mutableStateOf("No file selected") }

    // File Picker
    val filePickerLauncher = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.GetContent()
    ) { uri: Uri? ->
        if (uri != null) {
            fileName = "Document Selected" // Simplify for now
            viewModel.onFileSelected(uri)
        }
    }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(16.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.spacedBy(16.dp)
    ) {
        Text("Create New Story", style = MaterialTheme.typography.headlineMedium)

        // Section 1: Grade Level
        Text("1. Select Grade Level", style = MaterialTheme.typography.titleMedium, color = MaterialTheme.colorScheme.primary)
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceEvenly
        ) {
            listOf("K-2", "3-5", "6-8", "9-12").forEach { level ->
                FilterChip(
                    selected = grade == level,
                    onClick = { viewModel.setGrade(level) }, // Assuming ViewModel has setGrade
                    label = { Text(level) }
                )
            }
        }

        Spacer(modifier = Modifier.height(16.dp))

        // Section 2: File Upload
        Text("2. Upload Document", style = MaterialTheme.typography.titleMedium, color = MaterialTheme.colorScheme.primary)
        
        Card(
            modifier = Modifier
                .fillMaxWidth()
                .height(150.dp)
                .clickable { filePickerLauncher.launch("*/*") },
            colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant),
            border = androidx.compose.foundation.BorderStroke(1.dp, MaterialTheme.colorScheme.onSurfaceVariant) // Dotted effect requires custom draw, using solid for now
        ) {
            Column(
                modifier = Modifier.fillMaxSize(),
                verticalArrangement = Arrangement.Center,
                horizontalAlignment = Alignment.CenterHorizontally
            ) {
                Icon(
                    imageVector = Icons.Filled.Add,
                    contentDescription = "Upload",
                    modifier = Modifier.size(48.dp),
                    tint = MaterialTheme.colorScheme.primary
                )
                Spacer(modifier = Modifier.height(8.dp))
                Text(
                    text = if (fileName == "No file selected") "Tap to select PDF/DOCX" else fileName,
                    style = MaterialTheme.typography.bodyLarge
                )
            }
        }

        Spacer(modifier = Modifier.weight(1f))

        // Action Button
        Button(
            onClick = { viewModel.startProcess(context, token) },
            enabled = (createState is CreateState.Idle || createState is CreateState.Error) && fileName != "No file selected",
            modifier = Modifier.fillMaxWidth().height(56.dp)
        ) {
            Text("Generate Story", fontSize = 18.sp)
        }

        // Status
        when (val state = createState) {
            is CreateState.Idle -> {}
            is CreateState.Checking -> Text("Checking for duplicates...")
            is CreateState.DuplicateFound -> {
                AlertDialog(
                    onDismissRequest = {},
                    title = { Text("Already Exists") },
                    text = { Text("A story for this file already exists. Load it?") },
                    confirmButton = {
                        Button(onClick = { onStoryCreated(state.existingStoryId) }) {
                            Text("Load Existing")
                        }
                    },
                    dismissButton = {
                        Button(onClick = { viewModel.startProcess(context, token, forceNew = true) }) {
                            Text("Create New Anyway")
                        }
                    }
                )
            }
            is CreateState.Uploading -> CircularProgressIndicator()
            is CreateState.Generating -> {
                Column(horizontalAlignment = Alignment.CenterHorizontally) {
                    Text("Generating Story... ${state.progress}%")
                    LinearProgressIndicator(progress = state.progress / 100f)
                    Text(state.message, style = MaterialTheme.typography.bodySmall)
                }
            }
            is CreateState.Success -> {
                Text("Success! Finalizing...", color = Color.Green)
                // Auto navigate or save
                LaunchedEffect(Unit) {
                    // For now, treat JobID as StoryID. 
                    // In real implementation we need call save-story endpoint.
                     onStoryCreated(state.storyId)
                }
            }
            is CreateState.Error -> Text("Error: ${state.message}", color = Color.Red)
        }
        
        Spacer(modifier = Modifier.weight(1f))
        Button(onClick = onBack, colors = ButtonDefaults.buttonColors(containerColor = Color.Gray)) {
            Text("Cancel")
        }
    }
}
