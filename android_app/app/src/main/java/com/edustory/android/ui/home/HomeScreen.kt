package com.edustory.android.ui.home

import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.edustory.android.ui.components.GlassCard
import com.edustory.android.ui.components.GradientBackground
import com.edustory.android.ui.components.GradientText
import com.edustory.android.ui.theme.*

@Composable
fun HomeScreen(
    onNavigateToCreate: () -> Unit,
    onNavigateToLibrary: () -> Unit,
    onNavigateToOffline: () -> Unit
) {
    GradientBackground {
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(24.dp),
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.Top
        ) {
            Spacer(modifier = Modifier.height(48.dp))
            
            // Header Section
            Text(
                text = "Welcome Back",
                style = MaterialTheme.typography.headlineMedium,
                color = EduOnSurface,
                fontWeight = FontWeight.Medium
            )
            
            Spacer(modifier = Modifier.height(8.dp))
            
            // Gradient "EduStory" title matching web app
            GradientText(
                text = "EduStory",
                style = MaterialTheme.typography.displayLarge.copy(
                    fontWeight = FontWeight.ExtraBold,
                    letterSpacing = (-0.02).sp
                )
            )
            
            Spacer(modifier = Modifier.height(56.dp))

            // Dashboard Cards
            DashboardGlassCard(
                title = "📝 Create New Story",
                subtitle = "Upload PDF/DOCX and generate",
                borderColor = EduSecondary, // Pink
                onClick = onNavigateToCreate
            )
            
            Spacer(modifier = Modifier.height(20.dp))
            
            DashboardGlassCard(
                title = "📚 My Library",
                subtitle = "View your generated stories",
                borderColor = AccentBlue, // Blue
                onClick = onNavigateToLibrary
            )

            Spacer(modifier = Modifier.height(20.dp))

            DashboardGlassCard(
                title = "📱 Offline Stories",
                subtitle = "Access downloaded content",
                borderColor = AccentViolet, // Violet
                onClick = onNavigateToOffline
            )
        }
    }
}

@Composable
fun DashboardGlassCard(
    title: String,
    subtitle: String,
    borderColor: Color,
    onClick: () -> Unit
) {
    GlassCard(
        modifier = Modifier
            .fillMaxWidth()
            .height(120.dp),
        borderColor = borderColor,
        onClick = onClick
    ) {
        Column(
            modifier = Modifier.fillMaxSize(),
            verticalArrangement = Arrangement.Center
        ) {
            Text(
                text = title,
                style = MaterialTheme.typography.titleLarge,
                fontWeight = FontWeight.Bold,
                color = EduOnBackground,
                fontSize = 18.sp
            )
            
            Spacer(modifier = Modifier.height(6.dp))
            
            Text(
                text = subtitle,
                style = MaterialTheme.typography.bodyMedium,
                color = EduOnSurface,
                fontSize = 14.sp
            )
        }
    }
}
