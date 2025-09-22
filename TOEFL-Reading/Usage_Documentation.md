# TOEFL 2026 GenSheet Usage Documentation

This document provides instructions on how to use the TOEFL 2026 GenSheet Development project.

## Switching Between Models

You can switch between different model providers and models by editing the `Config` sheet in your Google Sheet.

1.  **Open the `Config` sheet** in your Google Sheet.
2.  **Set the `MODEL_PROVIDER`:** In the row for `MODEL_PROVIDER`, choose between "OpenAI", "Anthropic", or "Google".
3.  **Select the Model:**
    *   If you chose "OpenAI", go to the `OPENAI_MODEL` row and select the specific model you want to use (e.g., "gpt-4.1", "gpt-o4", "gpt-o4-mini").
    *   If you chose "Anthropic", go to the `ANTHROPIC_MODEL` row and select the specific model you want to use (e.g., "claude-3-opus-20240229", "claude-3-sonnet-20240229").
    *   If you chose "Google", go to the `GOOGLE_MODEL` row and select the specific model you want to use (e.g., "gemini-2.5-pro", "gemini-2.5-flash", "gemini-2.5-flash-lite", "gemini-live-2.5-flash-preview", "gemini-2.5-flash-preview-native-audio-dialog", "gemini-2.5-flash-exp-native-audio-thinking-dialog", "gemini-2.5-flash-image-preview", "gemini-2.5-flash-preview-tts", "gemini-2.5-pro-preview-tts").
4.  **Ensure API Keys are Set:** Make sure you have entered the correct API key for the selected provider in the corresponding `API_KEY` row (e.g., `ANTHROPIC_API_KEY`, `GOOGLE_API_KEY`).

Once you have made these changes in the `Config` sheet, the scripts will automatically use the selected model for the next generation.
