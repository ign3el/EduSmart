package com.edustory.android.ui.components

import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.ColumnScope
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.unit.dp
import com.edustory.android.ui.theme.Edge
import com.edustory.android.ui.theme.EduPrimary
import com.edustory.android.ui.theme.EduSurface

/**
 * Glass-effect card component matching web app glassmorphism design
 * 
 * Features:
 * - Semi-transparent background
 * - Colored border with glow effect
 * - Rounded corners (18dp)
 * - Clickable with ripple effect
 */
@Composable
fun GlassCard(
    modifier: Modifier = Modifier,
    borderColor: Color = EduPrimary,
    backgroundColor: Color = EduSurface.copy(alpha = 0.8f),
    onClick: (() -> Unit)? = null,
    content: @Composable ColumnScope.() -> Unit
) {
    Card(
        modifier = if (onClick != null) {
            modifier.clickable { onClick() }
        } else {
            modifier
        },
        colors = CardDefaults.cardColors(
            containerColor = backgroundColor
        ),
        border = BorderStroke(1.5.dp, borderColor.copy(alpha = 0.3f)),
        shape = RoundedCornerShape(18.dp),
        elevation = CardDefaults.cardElevation(
            defaultElevation = 8.dp,
            pressedElevation = 2.dp
        )
    ) {
        androidx.compose.foundation.layout.Column(
            modifier = Modifier.padding(20.dp),
            content = content
        )
    }
}
