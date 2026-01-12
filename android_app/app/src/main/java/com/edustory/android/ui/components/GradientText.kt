package com.edustory.android.ui.components

import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.TextStyle
import com.edustory.android.ui.theme.EduPrimary
import com.edustory.android.ui.theme.EduSecondary
import com.edustory.android.ui.theme.EduTertiary

/**
 * Text with gradient color effect matching web app gradient text
 * 
 * Default gradient: Purple -> Pink -> Cyan (matching web app header)
 */
@Composable
fun GradientText(
    text: String,
    modifier: Modifier = Modifier,
    style: TextStyle = MaterialTheme.typography.displayMedium,
    gradient: Brush = Brush.linearGradient(
        colors = listOf(
            EduPrimary,   // Purple
            EduSecondary, // Pink
            EduTertiary   // Cyan
        )
    )
) {
    Text(
        text = text,
        modifier = modifier,
        style = style.copy(
            brush = gradient
        )
    )
}
