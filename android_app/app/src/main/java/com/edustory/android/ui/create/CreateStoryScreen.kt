package com.edustory.android.ui.create

import android.net.Uri
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Add
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.lifecycle.viewmodel.compose.viewModel
import com.edustory.android.ui.components.GlassCard
import com.edustory.android.ui.components.GradientBackground
import com.edustory.android.ui.theme.*

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun CreateStoryScreen(
    token: String,
    onStoryCreated: (String) -> Unit,
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
            fileName = "Document Selected"
            viewModel.onFileSelected(uri)
        }
    }

    GradientBackground {
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(24.dp),
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.spacedBy(20.dp)
        ) {
            Spacer(modifier = Modifier.height(16.dp))
            
            Text(
                "Create New Story",
                style = MaterialTheme.typography.displaySmall,
                fontWeight = FontWeight.Bold,
                color = EduOnBackground
            )

            // Section 1: Grade Level in Glass Card
            GlassCard(
                modifier = Modifier.fillMaxWidth(),
                borderColor = EduPrimary
            ) {
                Column {
                    Text(
                        "1. Select Grade Level",
                        style = MaterialTheme.typography.titleMedium,
                        color = EduPrimary,
                        fontWeight = FontWeight.Bold
                    )
                    
                    Spacer(modifier = Modifier.height(12.dp))
                    
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceEvenly
                    ) {
                        listOf("K-2", "3-5", "6-8", "9-12").forEach { level ->
                            FilterChip(
                                selected = grade == level,
                                onClick = { viewModel.setGrade(level) },
                                label = { Text(level) },
                                colors = FilterChipDefaults.filterChipColors(
                                    selectedContainerColor = EduPrimary,
                                    selectedLabelColor = Color.White,
                                    containerColor = EduSurfaceVariant,
                                    labelColor = EduOnSurface
                                )
                            )
                        }
                    }
                }
            }

            // Section 2: File Upload in Glass Card
            GlassCard(
                modifier = Modifier.fillMaxWidth(),
                borderColor = EduSecondary
            ) {
                Column {
                    Text(
                        "2. Upload Document",
                        style = MaterialTheme.typography.titleMedium,
                        color = EduSecondary,
                        fontWeight = FontWeight.Bold
                    )
                    
                    Spacer(modifier = Modifier.height(12.dp))
                    
                    Card(
                        modifier = Modifier
                            .fillMaxWidth()
                            .height(140.dp)
                            .clickable { filePickerLauncher.launch("*/*") },
                        colors = CardDefaults.cardColors(
                            containerColor = EduSurfaceVariant.copy(alpha = 0.5f)
                        ),
                        border = BorderStroke(2.dp, Edge),
                        shape = RoundedCornerShape(12.dp)
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
                                tint = EduSecondary
                            )
                            Spacer(modifier = Modifier.height(8.dp))
                            Text(
                                text = if (fileName == "No file selected") "📄 Tap to select PDF/DOCX" else "✅ $fileName",
                                style = MaterialTheme.typography.bodyLarge,
                                color = EduOnSurface
                            )
                        }
                    }
                }
            }

            Spacer(modifier = Modifier.weight(1f))

            // Action Button
            Button(
                onClick = { viewModel.startProcess(context, token) },
                enabled = (createState is CreateState.Idle || createState is CreateState.Error) && fileName != "No file selected",
                modifier = Modifier
                    .fillMaxWidth()
                    .height(56.dp),
                colors = ButtonDefaults.buttonColors(
                    containerColor = EduPrimary,
                    disabledContainerColor = EduPrimary.copy(alpha = 0.5f)
                ),
                shape = RoundedCornerShape(12.dp)
            ) {
                Text(
                    "🚀 Generate Story",
                    fontSize = 18.sp,
                    fontWeight = FontWeight.Bold
                )
            }

            // Status
            when (val state = createState) {
                is CreateState.Idle -> {}
                is CreateState.Checking -> {
                    GlassCard(
                        modifier = Modifier.fillMaxWidth(),
                        borderColor = EduTertiary
                    ) {
                        Row(
                            verticalAlignment = Alignment.CenterVertically,
                            horizontalArrangement = Arrangement.spacedBy(12.dp)
                        ) {
                            CircularProgressIndicator(
                                modifier = Modifier.size(24.dp),
                                color = EduTertiary
                            )
                            Text("Checking for duplicates...", color = EduOnSurface)
                        }
                    }
                }
                is CreateState.DuplicateFound -> {
                    AlertDialog(
                        onDismissRequest = {},
                        title = { Text("Already Exists") },
                        text = { Text("A story for this file already exists. Load it?") },
                        confirmButton = {
                            Button(
                                onClick = { onStoryCreated(state.existingStoryId) },
                                colors = ButtonDefaults.buttonColors(containerColor = EduPrimary)
                            ) {
                                Text("Load Existing")
                            }
                        },
                        dismissButton = {
                            Button(
                                onClick = { viewModel.startProcess(context, token, forceNew = true) },
                                colors = ButtonDefaults.buttonColors(containerColor = EduSecondary)
                            ) {
                                Text("Create New Anyway")
                            }
                        },
                        containerColor = EduSurface,
                        titleContentColor = EduOnBackground,
                        textContentColor = EduOnSurface
                    )
                }
                is CreateState.Uploading -> {
                    GlassCard(
                        modifier = Modifier.fillMaxWidth(),
                        borderColor = EduPrimary
                    ) {
                        Row(
                            verticalAlignment = Alignment.CenterVertically,
                            horizontalArrangement = Arrangement.spacedBy(12.dp)
                        ) {
                            CircularProgressIndicator(
                                modifier = Modifier.size(24.dp),
                                color = EduPrimary
                            )
                            Text("Uploading...", color = EduOnSurface)
                        }
                    }
                }
                is CreateState.Generating -> {
                    GlassCard(
                        modifier = Modifier.fillMaxWidth(),
                        borderColor = EduSecondary
                    ) {
                        Column(horizontalAlignment = Alignment.CenterHorizontally) {
                            Text(
                                "Generating Story... ${state.progress}%",
                                style = MaterialTheme.typography.titleMedium,
                                color = EduOnBackground
                            )
                            Spacer(modifier = Modifier.height(12.dp))
                            LinearProgressIndicator(
                                progress = state.progress / 100f,
                                modifier = Modifier.fillMaxWidth(),
                                color = EduSecondary,
                                trackColor = EduSurfaceVariant
                            )
                            Spacer(modifier = Modifier.height(8.dp))
                            Text(
                                state.message,
                                style = MaterialTheme.typography.bodySmall,
                                color = EduOnSurface
                            )
                        }
                    }
                }
                is CreateState.Success -> {
                    GlassCard(
                        modifier = Modifier.fillMaxWidth(),
                        borderColor = EduTertiary
                    ) {
                        Text(
                            "✅ Success! Finalizing...",
                            color = EduTertiary,
                            style = MaterialTheme.typography.titleMedium
                        )
                    }
                    LaunchedEffect(Unit) {
                        onStoryCreated(state.storyId)
                    }
                }
                is CreateState.Error -> {
                    GlassCard(
                        modifier = Modifier.fillMaxWidth(),
                        borderColor = EduError
                    ) {
                        Text(
                            "❌ Error: ${state.message}",
                            color = EduError,
                            style = MaterialTheme.typography.bodyMedium
                        )
                    }
                }
            }
            
            Button(
                onClick = onBack,
                colors = ButtonDefaults.buttonColors(
                    containerColor = EduSurfaceVariant
                ),
                shape = RoundedCornerShape(12.dp),
                modifier = Modifier.fillMaxWidth()
            ) {
                Text("Cancel", color = EduOnSurface)
            }
        }
    }
}
