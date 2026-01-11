package com.edustory.android.ui.home

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Create
import androidx.compose.material.icons.filled.List
import androidx.compose.material.icons.filled.Warning // Using Warning as placeholder for Offline
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.edustory.android.ui.theme.*

@Composable
fun HomeScreen(
    onNavigateToCreate: () -> Unit,
    onNavigateToLibrary: () -> Unit,
    onNavigateToOffline: () -> Unit
) {
    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(16.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.Top
    ) {
        Spacer(modifier = Modifier.height(32.dp))
        
        // Header
        Text(
            text = "Welcome Back",
            style = MaterialTheme.typography.headlineMedium,
            color = MaterialTheme.colorScheme.onBackground
        )
        Text(
            text = "EduStory",
            style = MaterialTheme.typography.displayMedium,
            fontWeight = FontWeight.Bold,
            color = MaterialTheme.colorScheme.primary
        )
        
        Spacer(modifier = Modifier.height(48.dp))

        // Dashboard Options
        DashboardCard(
            title = "Create New Story",
            subtitle = "Upload PDF/DOCX and generate",
            icon = Icons.Filled.Create,
            color = MaterialTheme.colorScheme.primary, // Using theme primary
            onClick = onNavigateToCreate
        )
        
        Spacer(modifier = Modifier.height(16.dp))
        
        DashboardCard(
            title = "My Library",
            subtitle = "View your generated accounts",
            icon = Icons.Filled.List,
            color = MaterialTheme.colorScheme.secondary, // Using theme secondary
            onClick = onNavigateToLibrary
        )

        Spacer(modifier = Modifier.height(16.dp))

        DashboardCard(
            title = "Offline Stories",
            subtitle = "Access downloaded content",
            icon = Icons.Filled.Warning, // TODO: Replace with OfflinePin when available
            color = MaterialTheme.colorScheme.tertiary, // Using theme tertiary
            onClick = onNavigateToOffline
        )
    }
}

@Composable
fun DashboardCard(
    title: String,
    subtitle: String,
    icon: ImageVector,
    color: Color,
    onClick: () -> Unit
) {
    Card(
        colors = CardDefaults.cardColors(
            containerColor = MaterialTheme.colorScheme.surfaceVariant
        ),
        modifier = Modifier
            .fillMaxWidth()
            .height(110.dp)
            .clickable { onClick() }
    ) {
        Row(
            modifier = Modifier
                .fillMaxSize()
                .padding(16.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Icon(
                imageVector = icon,
                contentDescription = null,
                tint = color,
                modifier = Modifier.size(48.dp)
            )
            
            Spacer(modifier = Modifier.width(24.dp))
            
            Column {
                Text(
                    text = title,
                    style = MaterialTheme.typography.titleMedium,
                    fontWeight = FontWeight.Bold,
                    color = MaterialTheme.colorScheme.onSurface
                )
                Text(
                    text = subtitle,
                    style = MaterialTheme.typography.bodyMedium,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
            }
        }
    }
}
