#!/usr/bin/env node

/**
 * Browser automation daemon
 * Bridges Unix socket (AI client) <-> HTTP polling (Chrome extension)
 *
 * The extension polls GET /poll for commands and POSTs responses to /response.
 * The AI client connects via Unix socket to send commands and receive results.
 */

const fs = require('fs');
const path = require('path');
const net = require('net');
const http = require('http');

// Configuration from environment or defaults
const SAK_HOME = process.env.SAK_HOME || path.join(require('os').homedir(), '.sovereign-ai');
const SKILL_DIR = process.env.SAK_BROWSER_SKILL_DIR || path.join(SAK_HOME, 'browser');
const HTTP_PORT = parseInt(process.env.SAK_BROWSER_PORT || process.argv[2] || '19222', 10);
const LOG_FILE = path.join(SKILL_DIR, 'daemon.log');
const SOCKET_PATH = path.join(SKILL_DIR, 'browser.sock');

let pendingRequests = new Map(); // requestId -> {socket, timeout}

function log(message) {
  const timestamp = new Date().toISOString();
  try {
    fs.mkdirSync(path.dirname(LOG_FILE), { recursive: true });
    fs.appendFileSync(LOG_FILE, `[${timestamp}] ${message}\n`);
  } catch (e) {
    // Silently fail logging
  }
}

let commandQueue = [];

function startHttpServer() {
  const httpServer = http.createServer((req, res) => {
    let body = '';
    req.on('data', chunk => body += chunk);
    req.on('end', () => {
      try {
        if (req.method === 'GET' && req.url === '/poll') {
          if (commandQueue.length > 0) {
            const command = commandQueue.shift();
            log(`Sending command to extension: ${JSON.stringify(command)}`);
            res.writeHead(200, { 'Content-Type': 'application/json' });
            res.end(JSON.stringify(command));
          } else {
            res.writeHead(204);
            res.end();
          }
        } else if (req.method === 'POST' && req.url === '/response') {
          const response = JSON.parse(body);
          log(`Received response from extension: ${JSON.stringify(response)}`);

          const { requestId } = response;
          if (pendingRequests.has(requestId)) {
            const { socket, timeout } = pendingRequests.get(requestId);
            clearTimeout(timeout);
            pendingRequests.delete(requestId);
            socket.write(JSON.stringify(response) + '\n');
            log(`Sent response to client for request ${requestId}`);
          }

          res.writeHead(200);
          res.end('OK');
        } else if (req.method === 'GET' && req.url === '/health') {
          res.writeHead(200, { 'Content-Type': 'application/json' });
          res.end(JSON.stringify({
            status: 'ok',
            pending: pendingRequests.size,
            queued: commandQueue.length
          }));
        } else {
          res.writeHead(404);
          res.end('Not found');
        }
      } catch (err) {
        log(`HTTP error: ${err.message}`);
        res.writeHead(500);
        res.end(err.message);
      }
    });
  });

  httpServer.listen(HTTP_PORT, '127.0.0.1', () => {
    log(`HTTP server listening on http://127.0.0.1:${HTTP_PORT}`);
  });

  httpServer.on('error', (err) => {
    if (err.code === 'EADDRINUSE') {
      log(`Port ${HTTP_PORT} in use - daemon already running?`);
      process.exit(1);
    }
    log(`HTTP server error: ${err.message}`);
  });
}

function startSocketServer() {
  try {
    if (fs.existsSync(SOCKET_PATH)) {
      fs.unlinkSync(SOCKET_PATH);
    }
  } catch (err) {
    log(`Error cleaning socket: ${err.message}`);
  }

  const server = net.createServer((socket) => {
    log('AI client connected');
    let buffer = '';

    socket.on('data', (data) => {
      buffer += data.toString();
      const lines = buffer.split('\n');
      buffer = lines.pop();

      for (const line of lines) {
        if (!line.trim()) continue;
        try {
          const command = JSON.parse(line);
          log(`Received command: ${JSON.stringify(command)}`);

          const timeout = setTimeout(() => {
            if (pendingRequests.has(command.requestId)) {
              pendingRequests.delete(command.requestId);
              socket.write(JSON.stringify({
                requestId: command.requestId,
                success: false,
                error: 'Timeout waiting for extension response'
              }) + '\n');
            }
          }, 30000);

          pendingRequests.set(command.requestId, { socket, timeout });
          commandQueue.push(command);
          log(`Queued command ${command.requestId} for extension pickup`);
        } catch (err) {
          log(`Error processing command: ${err.message}`);
          socket.write(JSON.stringify({ success: false, error: err.message }) + '\n');
        }
      }
    });

    socket.on('end', () => log('AI client disconnected'));
    socket.on('error', (err) => log(`Socket error: ${err.message}`));
  });

  server.listen(SOCKET_PATH, () => {
    log(`Socket server listening on ${SOCKET_PATH}`);
    fs.chmodSync(SOCKET_PATH, 0o666);
  });

  server.on('error', (err) => log(`Server error: ${err.message}`));
}

if (require.main === module) {
  log('Browser daemon starting...');

  process.on('SIGTERM', () => { log('Received SIGTERM, shutting down'); process.exit(0); });
  process.on('SIGINT', () => { log('Received SIGINT, shutting down'); process.exit(0); });

  // Ensure skill directory exists
  fs.mkdirSync(SKILL_DIR, { recursive: true });

  startSocketServer();
  startHttpServer();

  log('Browser daemon fully initialized');
}

module.exports = { log };
