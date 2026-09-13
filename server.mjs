// Optional local preview. No dependencies; binds only to this computer.
import http from 'node:http';
import { createReadStream } from 'node:fs';
import { stat } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const root = path.dirname(fileURLToPath(import.meta.url));
const allowed = new Set(['index.html', 'original.html', 'reader.css', 'app.mjs', 'book.js', 'viewer.mjs', 'assets/book-zh.pdf']);
const types = { '.html': 'text/html; charset=utf-8', '.js': 'text/javascript; charset=utf-8', '.mjs': 'text/javascript; charset=utf-8', '.css': 'text/css', '.json':'application/json; charset=utf-8', '.mp3':'audio/mpeg', '.png':'image/png', '.jpg':'image/jpeg', '.svg':'image/svg+xml', '.woff2':'font/woff2', '.wasm': 'application/wasm', '.pdf': 'application/pdf', '.ly':'text/plain; charset=utf-8' };
const server = http.createServer(async (req, res) => {
  try {
    if (!['GET', 'HEAD'].includes(req.method)) { res.writeHead(405).end(); return; }
    const key = decodeURIComponent(new URL(req.url, 'http://localhost').pathname).slice(1) || 'index.html';
    const vendor = ['vendor/pdfjs/','vendor/katex/','assets/','content/'].some(prefix=>key.startsWith(prefix)) && !key.includes('..') && !key.includes('\\') && !key.endsWith('.tex');
    if (!allowed.has(key) && !vendor) { res.writeHead(404).end('Not found'); return; }
    const file = path.join(root, key);
    const { size } = await stat(file);
    let start = 0, end = size - 1, status = 200;
    if (req.headers.range) {
      const match = /^bytes=(\d+)-(\d*)$/.exec(req.headers.range);
      if (!match) { res.writeHead(416, { 'Content-Range': `bytes */${size}` }).end(); return; }
      start = Number(match[1]);
      end = match[2] ? Math.min(Number(match[2]), end) : end;
      if (start > end || start >= size) { res.writeHead(416, { 'Content-Range': `bytes */${size}` }).end(); return; }
      status = 206;
    }
    const headers = { 'Content-Type': types[path.extname(file)] || 'application/octet-stream', 'Content-Length': end - start + 1, 'Accept-Ranges': 'bytes', 'X-Content-Type-Options': 'nosniff' };
    if (status === 206) headers['Content-Range'] = `bytes ${start}-${end}/${size}`;
    res.writeHead(status, headers);
    if (req.method === 'HEAD') { res.end(); return; }
    const stream = createReadStream(file, { start, end });
    stream.on('error', () => res.destroy());
    res.on('close', () => stream.destroy());
    stream.pipe(res);
  } catch { if (!res.headersSent) res.writeHead(500); res.end(); }
});
server.listen(4173, '127.0.0.1', () => console.log('http://127.0.0.1:4173'));
