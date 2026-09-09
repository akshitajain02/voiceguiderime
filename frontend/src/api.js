// src/api.js

export async function askAssistant(screenData, userQuery) {
  const { buildPrompt } = await import("./promptBuilder.js");
  const prompt = buildPrompt(screenData, userQuery);

  try {
    const response = await fetch("http://localhost:8000/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ prompt }),
    });

    if (!response.ok) throw new Error("Backend error: " + response.status);

    const data = await response.json();
    return data.reply;
  } catch (err) {
    console.error("askAssistant failed:", err);
    return "Sorry, main abhi jawab nahi de pa raha. Dobara try karo.";
  }
}