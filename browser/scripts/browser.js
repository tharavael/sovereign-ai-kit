#!/usr/bin/env node

/**
 * CLI wrapper for browser automation
 * Sends commands to extension via Unix socket through the daemon
 *
 * Usage: browser.js <command> [args...]
 */

const net = require('net');
const path = require('path');
const os = require('os');

const SAK_HOME = process.env.SAK_HOME || path.join(os.homedir(), '.sovereign-ai');
const SKILL_DIR = process.env.SAK_BROWSER_SKILL_DIR || path.join(SAK_HOME, 'browser');
const SOCKET_PATH = path.join(SKILL_DIR, 'browser.sock');

function sendCommand(command, args) {
  return new Promise((resolve, reject) => {
    const client = net.createConnection(SOCKET_PATH, () => {
      let commandObj = { type: command, data: {}, requestId: Date.now() };

      switch (command) {
        case 'navigate':
          commandObj.data = { url: args[0], tabId: args[1] ? parseInt(args[1]) : null };
          break;
        case 'query':
          commandObj.data = {
            selector: args[0],
            mode: args[1] || 'list',
            options: args[2] ? JSON.parse(args[2]) : {}
          };
          break;
        case 'click':
          commandObj.data = {
            selector: args[0],
            index: args[1] ? parseInt(args[1]) : 0,
            tabId: args[2] ? parseInt(args[2]) : null
          };
          break;
        case 'type':
          commandObj.data = {
            selector: args[0],
            text: args[1],
            tabId: args[2] ? parseInt(args[2]) : null
          };
          break;
        case 'screenshot':
          commandObj.data = { tabId: args[0] ? parseInt(args[0]) : null };
          break;
        case 'get_tabs':
          commandObj.data = {};
          break;
        case 'open_tab':
          commandObj.data = { url: args[0], active: args[1] !== 'false' };
          break;
        case 'close_tab':
          commandObj.data = { tabId: parseInt(args[0]) };
          break;
        default:
          reject(new Error(`Unknown command: ${command}`));
          return;
      }

      client.write(JSON.stringify(commandObj) + '\n');
    });

    let response = '';

    client.on('data', (data) => {
      response += data.toString();
      if (response.includes('\n')) {
        try {
          const result = JSON.parse(response.trim());
          client.end();
          resolve(result);
        } catch (err) {
          // Wait for more data
        }
      }
    });

    client.on('end', () => {
      if (response) {
        try { resolve(JSON.parse(response.trim())); }
        catch (err) { reject(new Error('Invalid response from daemon')); }
      }
    });

    client.on('error', (err) => {
      if (err.code === 'ENOENT' || err.code === 'ECONNREFUSED') {
        reject(new Error('Browser daemon not running. Start it with: start-daemon.sh'));
      } else {
        reject(err);
      }
    });

    client.setTimeout(30000, () => {
      client.destroy();
      reject(new Error('Command timeout'));
    });
  });
}

async function main() {
  const [command, ...args] = process.argv.slice(2);

  if (!command) {
    console.error('Usage: browser.js <command> [args...]');
    console.error('\nCommands:');
    console.error('  navigate <url>              Load a URL');
    console.error('  query <selector> [mode]     Query DOM elements');
    console.error('  click <selector> [index]    Click an element');
    console.error('  type <selector> <text>      Type text into element');
    console.error('  screenshot                  Capture visible tab');
    console.error('  get_tabs                    List all tabs');
    console.error('  open_tab <url> [active]     Open new tab');
    console.error('  close_tab <tabId>           Close tab');
    console.error('\nQuery modes: list, text, value, exists, page_text, html');
    process.exit(1);
  }

  try {
    const result = await sendCommand(command, args);
    console.log(JSON.stringify(result, null, 2));
  } catch (error) {
    console.error('Error:', error.message);
    process.exit(1);
  }
}

if (require.main === module) {
  main();
}

module.exports = { sendCommand };
