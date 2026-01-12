package com.edustory.android.ui.offline

import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.Modifier
import com.edustory.android.ui.components.GlassCard
import com.edustory.android.ui.components.GradientBackground
import com.edustory.android.ui.theme.*

@Composable
fun OfflineLibraryScreen(
    onBack: () -> Unit
) {
    GradientBackground {
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(24.dp)
        ) {
            Text(
                text = "📱 Offline Library",
                style = MaterialTheme.typography.displaySmall,
                fontWeight = FontWeight.Bold,
                color = EduOnBackground
            )
            
            Spacer(modifier = Modifier.height(32.dp))
            
            Box(
                modifier = Modifier.fillMaxSize(),
                contentAlignment = Alignment.Center
            ) {
                GlassCard(
                    borderColor = AccentViolet
                ) {
                    Column(
                        horizontalAlignment = Alignment.CenterHorizontally,
                        modifier = Modifier.padding(16.dp)
                    ) {
                        Text(
                            text = "📥 No offline stories found",
                            style = MaterialTheme.typography.titleLarge,
                            color = EduOnBackground,
                            fontWeight = FontWeight.Bold
                        )
                        Spacer(modifier = Modifier.height(8.dp))
                        Text(
                            text = "(Implementation Pending)",
                            style = MaterialTheme.typography.bodyMedium,
                            color = EduOnSurface
                        )
                    }
                }
            }
        }
    }
}
