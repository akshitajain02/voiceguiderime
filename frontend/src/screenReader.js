// src/screenReader.js
// Ye function current webpage ka "screen-reader jaisa" summary banata hai —
// visually impaired user ke liye screen pe kya hai wo LLM ko batane ke liye.

export function readCurrentPage() {
  const meaningfulSelectors = [
    "button", "a", "input", "select", "textarea",
    "h1", "h2", "h3", "h4", "h5", "h6",
    "[role]", "img[alt]", "label", "p"
  ];

  const elements = document.querySelectorAll(meaningfulSelectors.join(","));
  const pageContent = [];

  elements.forEach((el) => {
    const rect = el.getBoundingClientRect();
    const isVisible =
      rect.width > 0 &&
      rect.height > 0 &&
      window.getComputedStyle(el).visibility !== "hidden" &&
      window.getComputedStyle(el).display !== "none";

    if (!isVisible) return;

    const tag = el.tagName.toLowerCase();
    const role = el.getAttribute("role") || tag;
    const text =
      el.innerText?.trim() ||
      el.getAttribute("aria-label") ||
      el.getAttribute("alt") ||
      el.getAttribute("placeholder") ||
      "";

    if (!text) return;

    pageContent.push({
      role,
      text: text.slice(0, 150),
      position: {
        top: Math.round(rect.top),
        left: Math.round(rect.left),
      },
    });
  });

  const summary = pageContent
    .map((el) => `[${el.role}] ${el.text}`)
    .join("\n");

  return {
    url: window.location.href,
    title: document.title,
    elements: pageContent,
    summaryText: summary,
  };
}