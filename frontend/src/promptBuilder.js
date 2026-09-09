// src/promptBuilder.js
// Ye "LLM prompt design" ka core hai — screen-content + user query ko
// ek structured prompt mein badalta hai jisse LLM sahi decision le sake
// ki user ko kya bolna hai (voice ke through).

export function buildPrompt(screenData, userQuery) {
  // Agar screen pe kuch relevant nahi mila, LLM ko clearly bata do
  const hasContent = screenData.elements && screenData.elements.length > 0;

  return `You are a voice assistant helping a visually impaired user navigate a webpage in real time.

=== CURRENT SCREEN CONTEXT ===
Page title: "${screenData.title}"
URL: ${screenData.url}

Visible elements on screen (in reading order):
${hasContent ? screenData.summaryText : "(No readable elements detected on this screen)"}

=== USER'S SPOKEN QUESTION ===
"${userQuery}"

=== YOUR TASK ===
Decide the single best spoken response to help the user right now. Follow these rules strictly:
1. Base your answer ONLY on the screen elements listed above — never invent buttons, links, or fields that aren't listed.
2. If the user is asking "where is X" or "how do I do X", identify the matching element by its [role] and text, and describe its position in simple terms (e.g. "top of the screen", "below the username field").
3. If nothing on screen matches the user's request, say so directly and briefly mention what IS available instead.
4. Keep your response to 1-2 short sentences maximum — it will be converted to speech and read aloud.
5. Do not use markdown, bullet points, or symbols — plain spoken language only.

Respond now with only the spoken response, nothing else:`;
}