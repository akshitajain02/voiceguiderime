# Frontend — Abhayraj's Module

This folder is owned by **Abhayraj**.

## What to build
1. Web app UI (HTML/CSS/JS or React)
2. Demo pages with DOM/accessibility-tree extraction ("read current page" JS function)
3. LLM prompt design — screen_content + user query → decide what to respond
4. LiveKit data-channel sender (sends screen_content JSON to voice-agent)

## Integration point
Your JS code sends screen data to the LiveKit room via data-channel:
```javascript
room.localParticipant.publishData(JSON.stringify({
  screen_content: {
    app_name: document.title,
    elements: extractedElements,
    raw_text: document.body.innerText.substring(0, 2000)
  }
}), { reliable: true });
```

## Key files to create
- `index.html` — Main web app entry
- `app.js` — Core application logic
- `screen_reader.js` — DOM/accessibility extraction
- `livekit_client.js` — LiveKit room connection + data-channel
- `styles.css` — UI styling
