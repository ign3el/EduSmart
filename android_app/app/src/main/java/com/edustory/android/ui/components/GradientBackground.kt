package com.edustory.android.ui.components

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import com.edustory.android.ui.theme.*

/**
 * Multi-layer gradient background matching web app design
 * 
 * Features:
 * - Base linear gradient (Canvas -> Panel)
 * - Multiple radial gradient overlays
 * - Purple, pink, and blue accent glows
 */
@Composable
fun GradientBackground(
    modifier: Modifier = Modifier,
    content: @Composable () -> Unit
) {
    Box(
        modifier = modifier
            .fillMaxSize()
            // Layer 1: Radial gradient (top-left purple glow)
            .background(
                Brush.radialGradient(
                    colors = listOf(
                        EduPrimary.copy(alpha = 0.15f),
                        Color.Transparent
                    ),
                    center = Offset(0.1f, 0.1f),
                    radius = 800f
                )
            )
            // Layer 2: Radial gradient (bottom-right pink glow)
            .background(
                Brush.radialGradient(
                    colors = listOf(
                        EduSecondary.copy(alpha = 0.12f),
                        Color.Transparent
                    ),
                    center = Offset(0.85f, 0.85f),
                    radius = 900f
                )
            )
            // Layer 3: Radial gradient (top-right blue glow)
            .background(
                Brush.radialGradient(
                    colors = listOf(
                        AccentBlue.copy(alpha = 0.1f),
                        Color.Transparent
                    ),
                    center = Offset(0.9f, 0.1f),
                    radius = 1000f
                )
            )
            // Base layer: Linear gradient
            .background(
                Brush.linearGradient(
                    colors = listOf(
                        EduBackground,
                        EduSurface
                    )
                )
            )
    ) {
        content()
    }
}
