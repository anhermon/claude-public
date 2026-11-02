// Tiny static server WITH HTTP Range support (video scrubbing cannot seek without it; python -m http.server has none).
// node serve-range.mjs [port=8731] [root=.]
import { createServer } from 'node:http';
import { createReadStream, statSync } from 'node:fs';
import path from 'node:path';

const MIME = { '.html': 'text/html', '.js': 'text/javascript', '.json': 'application/json', '.mp4': 'video/mp4', '.webm': 'video/webm',
  '.jpg': 'image/jpeg', '.png': 'image/png', '.webp': 'image/webp', '.avif': 'image/avif', '.css': 'text/css' };
const PORT = Number(process.argv[2] || 8731);
const ROOT = path.resolve(process.argv[3] || '.');
const OK = 200, PARTIAL = 206, NOT_FOUND = 404, BAD_RANGE = 416;

createServer((req, res) => {
  const file = path.join(ROOT, decodeURIComponent(new URL(req.url, 'http://x').pathname));
  let st;
  try { st = statSync(file); if (st.isDirectory()) throw new Error('dir'); } catch { res.writeHead(NOT_FOUND).end('not found'); return; }
  if (!file.startsWith(ROOT)) { res.writeHead(NOT_FOUND).end(); return; }
  const head = { 'Content-Type': MIME[path.extname(file)] || 'application/octet-stream', 'Accept-Ranges': 'bytes' };
  const m = /bytes=(\d*)-(\d*)/.exec(req.headers.range || '');
  if (!m) { res.writeHead(OK, { ...head, 'Content-Length': st.size }); createReadStream(file).pipe(res); return; }
  const start = m[1] ? Number(m[1]) : st.size - Number(m[2]);
  const end = m[1] && m[2] ? Number(m[2]) : st.size - 1;
  if (start > end || end >= st.size) { res.writeHead(BAD_RANGE, { 'Content-Range': `bytes */${st.size}` }).end(); return; }
  res.writeHead(PARTIAL, { ...head, 'Content-Range': `bytes ${start}-${end}/${st.size}`, 'Content-Length': end - start + 1 });
  createReadStream(file, { start, end }).pipe(res);
}).listen(PORT, '127.0.0.1', () => console.log(`serving ${ROOT} on :${PORT}`));
