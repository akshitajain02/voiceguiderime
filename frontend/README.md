 backend-prajjwal_baweja
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

# React + Vite

This template provides a minimal setup to get React working in Vite with HMR and some Oxlint rules.

Currently, two official plugins are available:

- [@vitejs/plugin-react](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react) uses [Oxc](https://oxc.rs)
- [@vitejs/plugin-react-swc](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react-swc) uses [SWC](https://swc.rs/)

## React Compiler

The React Compiler is not enabled on this template because of its impact on dev & build performances. To add it, see [this documentation](https://react.dev/learn/react-compiler/installation).

## Expanding the Oxlint configuration

If you are developing a production application, we recommend using TypeScript with type-aware lint rules enabled. Check out the [TS template](https://github.com/vitejs/vite/tree/main/packages/create-vite/template-react-ts) for information on how to integrate TypeScript and Oxlint's TypeScript related rules in your project.
main
