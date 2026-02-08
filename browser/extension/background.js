// Browser automation extension - service worker
// Uses HTTP polling to communicate with daemon (avoids native messaging lifecycle issues)

// Port is configurable via chrome.storage, defaults to 19222
let DAEMON_PORT = 19222;
let DAEMON_URL = `http://127.0.0.1:${DAEMON_PORT}`;

const ALARM_NAME = 'daemon-poll';
let sessionData = { tabs: {}, activeTabId: null };
let isPolling = false;

// Load configured port from storage
chrome.storage.local.get(['daemon_port'], (result) => {
  if (result.daemon_port) {
    DAEMON_PORT = result.daemon_port;
    DAEMON_URL = `http://127.0.0.1:${DAEMON_PORT}`;
  }
});

chrome.runtime.onStartup.addListener(() => startPolling());

chrome.runtime.onInstalled.addListener(() => {
  console.log('Sovereign AI Browser Agent installed');
  startPolling();
});

chrome.alarms.onAlarm.addListener((alarm) => {
  if (alarm.name === ALARM_NAME) pollOnce();
});

function startPolling() {
  console.log(`Polling daemon on port ${DAEMON_PORT}...`);
  chrome.alarms.create(ALARM_NAME, { periodInMinutes: 0.0834 }); // ~5 seconds
  pollOnce();
}

async function pollOnce() {
  if (isPolling) return;
  isPolling = true;

  try {
    const burstEnd = Date.now() + 5000;
    while (Date.now() < burstEnd) {
      const hasCommand = await pollDaemon();
      if (!hasCommand) {
        await new Promise(r => setTimeout(r, 100));
      }
    }
  } catch (error) {
    // Ignore fetch errors (daemon not running)
  } finally {
    isPolling = false;
  }
}

async function pollDaemon() {
  try {
    const response = await fetch(`${DAEMON_URL}/poll`, {
      method: 'GET',
      headers: { 'Accept': 'application/json' }
    });

    if (response.status === 204) return false;

    if (response.ok) {
      const command = await response.json();
      console.log('Received command:', command);

      try {
        const result = await handleMessage(command);
        await fetch(`${DAEMON_URL}/response`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(result)
        });
      } catch (error) {
        console.error('Error handling command:', error);
        await fetch(`${DAEMON_URL}/response`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            requestId: command.requestId,
            success: false,
            error: error.message
          })
        });
      }
      return true;
    }
  } catch (error) {
    if (!error.message.includes('Failed to fetch')) {
      console.log('Poll error:', error.message);
    }
  }
  return false;
}

async function handleMessage(message) {
  const { type: msgType, data, requestId } = message;

  try {
    let result;

    switch (msgType) {
      case 'navigate':   result = await navigate(data.url, data.tabId); break;
      case 'query':      result = await query(data.selector, data.mode, data.options); break;
      case 'click':      result = await click(data.selector, data.index, data.tabId); break;
      case 'type':       result = await typeText(data.selector, data.text, data.tabId); break;
      case 'screenshot': result = await screenshot(data.tabId); break;
      case 'get_tabs':   result = await getTabs(); break;
      case 'open_tab':   result = await openTab(data.url, data.active); break;
      case 'close_tab':  result = await closeTab(data.tabId); break;
      case 'get_session': result = sessionData; break;
      default: throw new Error(`Unknown message type: ${msgType}`);
    }

    return { requestId, success: true, data: result };
  } catch (error) {
    return { requestId, success: false, error: error.message, stack: error.stack };
  }
}

// ── Commands ──────────────────────────────────────────────

async function navigate(url, tabId) {
  const tab = tabId
    ? await chrome.tabs.get(tabId)
    : (await chrome.tabs.query({ active: true, currentWindow: true }))[0];

  await chrome.tabs.update(tab.id, { url });

  await new Promise((resolve) => {
    const listener = (tId, info) => {
      if (tId === tab.id && info.status === 'complete') {
        chrome.tabs.onUpdated.removeListener(listener);
        resolve();
      }
    };
    chrome.tabs.onUpdated.addListener(listener);
  });

  sessionData.activeTabId = tab.id;
  return { tabId: tab.id, url };
}

async function query(selector, mode = 'list', options = {}) {
  const tab = await getActiveTab();
  const results = await chrome.scripting.executeScript({
    target: { tabId: tab.id },
    func: queryDOM,
    args: [selector, mode, options]
  });
  return results[0].result;
}

function queryDOM(selector, mode, options) {
  const elements = document.querySelectorAll(selector);

  switch (mode) {
    case 'list':
      return Array.from(elements).map((el, index) => ({
        index,
        tagName: el.tagName.toLowerCase(),
        text: el.textContent?.trim().substring(0, 100) || '',
        value: el.value || '',
        href: el.href || '',
        visible: el.offsetParent !== null
      }));
    case 'text':
      return elements[0]?.textContent?.trim() || '';
    case 'value':
      return elements[0]?.value || '';
    case 'exists':
      return { exists: elements.length > 0, count: elements.length };
    case 'page_text':
      return document.body.innerText;
    case 'html':
      return Array.from(elements).map(el => el.outerHTML);
    default:
      return Array.from(elements).map(el => el.outerHTML);
  }
}

async function click(selector, index = 0, tabId) {
  const tab = tabId ? await chrome.tabs.get(tabId) : await getActiveTab();
  await chrome.scripting.executeScript({
    target: { tabId: tab.id },
    func: (sel, idx) => {
      const elements = document.querySelectorAll(sel);
      if (elements[idx]) { elements[idx].click(); return true; }
      throw new Error(`Element not found: ${sel} at index ${idx}`);
    },
    args: [selector, index]
  });
  return { clicked: true, selector, index };
}

async function typeText(selector, text, tabId) {
  const tab = tabId ? await chrome.tabs.get(tabId) : await getActiveTab();
  await chrome.scripting.executeScript({
    target: { tabId: tab.id },
    func: (sel, txt) => {
      const element = document.querySelector(sel);
      if (element) {
        element.value = txt;
        element.dispatchEvent(new Event('input', { bubbles: true }));
        element.dispatchEvent(new Event('change', { bubbles: true }));
        return true;
      }
      throw new Error(`Element not found: ${sel}`);
    },
    args: [selector, text]
  });
  return { typed: true, selector, text: text.substring(0, 50) };
}

async function screenshot(tabId) {
  const tab = tabId ? await chrome.tabs.get(tabId) : await getActiveTab();
  const dataUrl = await chrome.tabs.captureVisibleTab(tab.windowId, { format: 'png' });
  return { dataUrl, tabId: tab.id };
}

async function getTabs() {
  const tabs = await chrome.tabs.query({});
  return tabs.map(tab => ({
    id: tab.id, url: tab.url, title: tab.title,
    active: tab.active, windowId: tab.windowId
  }));
}

async function openTab(url, active = true) {
  const tab = await chrome.tabs.create({ url, active });
  sessionData.tabs[tab.id] = { url, created: Date.now() };
  if (active) sessionData.activeTabId = tab.id;
  return { tabId: tab.id, url: tab.url };
}

async function closeTab(tabId) {
  await chrome.tabs.remove(tabId);
  delete sessionData.tabs[tabId];
  return { closed: true, tabId };
}

async function getActiveTab() {
  const tabs = await chrome.tabs.query({ active: true, currentWindow: true });
  if (!tabs[0]) throw new Error('No active tab found');
  return tabs[0];
}

startPolling();
