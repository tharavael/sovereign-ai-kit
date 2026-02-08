// Content script - marks page as having the extension active
// Minimal footprint; DOM operations are injected via chrome.scripting from background.js

if (!window.__sovereignAIBrowserAgent) {
  window.__sovereignAIBrowserAgent = true;
}
