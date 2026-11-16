// Test-only static server (zero deps). Usage: node serve.mjs <root> [port=8790]
// - Cache-Control: no-store (Simulator Safari caches hard).
// - Analytics never leave a test: same-origin scripts whose path matches ANALYTICS are served as a no-op stub, and
//   <script> tags (external or inline) mentioning a tracker are stripped from HTML. The Simulator cannot block
//   requests itself, so this server is the only defence there.
// - Injects a probe into HTML (skip with ?noprobe): ?sel=<css>&off=<px> scrolls to an element, ?vh=<n> scrolls n
//   viewport heights, ?y=<px>; &d=<ms> delays the scroll. After load it POSTs a state report to /log
//   (appended to $TMPDIR/premium-web-serve-<port>.jsonl; shoot.sh reads it). Busy port -> next free one.
import http from "node:http";
import fs from "node:fs";
import path from "node:path";
import os from "node:os";

const ROOT = path.resolve(process.argv[2] || ".");
let PORT = +(process.argv[3] || process.env.PORT || 8790);
const logFor = (port) => process.env.LOG || path.join(os.tmpdir(), `premium-web-serve-${port}.jsonl`); // per port: other agents may run this script at the same time
let LOG = logFor(PORT);
const ANALYTICS = new RegExp(process.env.ANALYTICS || "posthog|analytics|gtag|googletagmanager|google-analytics|plausible|segment|mixpanel|hotjar|clarity", "i");
const TYPES = { ".html": "text/html; charset=utf-8", ".css": "text/css", ".js": "text/javascript", ".mjs": "text/javascript", ".json": "application/json", ".svg": "image/svg+xml", ".png": "image/png", ".jpg": "image/jpeg", ".webp": "image/webp", ".avif": "image/avif", ".woff2": "font/woff2", ".txt": "text/plain", ".xml": "application/xml", ".ico": "image/x-icon", ".mp4": "video/mp4", ".webm": "video/webm" };

const PROBE = `<script>(function(){
var q=new URLSearchParams(location.search),errs=[];window.__analyticsBlocked=true;
addEventListener('error',function(e){errs.push(String(e.message||e))});
addEventListener('unhandledrejection',function(e){errs.push('rejection: '+String(e.reason))});
function report(tag){var fonts=[];try{document.fonts.forEach(function(f){fonts.push(f.family.replace(/"/g,'')+' '+f.weight+' '+f.status)})}catch(e){}
var wide=[].slice.call(document.querySelectorAll('body *')).filter(function(e){return e.getBoundingClientRect().right>innerWidth+1}).slice(0,5).map(function(e){return e.tagName+'.'+String(e.className).slice(0,30)});
fetch('/log',{method:'POST',body:JSON.stringify({tag:tag,url:location.href,ua:navigator.userAgent,w:innerWidth,h:innerHeight,sw:document.documentElement.scrollWidth,y:Math.round(scrollY),fonts:fonts,wide:wide,errs:errs,rm:matchMedia('(prefers-reduced-motion: reduce)').matches,dark:matchMedia('(prefers-color-scheme: dark)').matches,state:document.documentElement.dataset})}).catch(function(){})}
addEventListener('load',function(){var d=+(q.get('d')||600);
setTimeout(function(){var y=null;if(q.has('y'))y=+q.get('y');if(q.has('vh'))y=+q.get('vh')*innerHeight;
if(q.has('sel')){var el=document.querySelector(q.get('sel'));if(el)y=el.getBoundingClientRect().top+scrollY+(+(q.get('off')||0))}
if(y!=null){document.documentElement.style.scrollBehavior='auto';scrollTo(0,y)}
setTimeout(function(){report('load')},1200)},d)});
})();</script>`;

function stripTrackers(html) {
  return html.replace(/<script\b[^>]*>[\s\S]*?<\/script>/gi, (tag) => (ANALYTICS.test(tag) && !tag.includes("__analyticsBlocked") ? "<!-- tracker stripped by serve.mjs -->" : tag));
}

const server = http.createServer((req, res) => {
  const u = new URL(req.url, "http://x");
  const h = { "Cache-Control": "no-store" };
  if (req.method === "POST" && u.pathname === "/log") {
    let b = ""; req.on("data", (c) => (b += c));
    req.on("end", () => { fs.appendFileSync(LOG, b + "\n"); res.writeHead(204, h); res.end(); });
    return;
  }
  let p = decodeURIComponent(u.pathname);
  if (p.endsWith("/")) p += "index.html";
  const f = path.join(ROOT, p);
  if (!f.startsWith(ROOT)) { res.writeHead(403, h); return res.end(); }
  if (/\.m?js$/.test(p) && ANALYTICS.test(p)) { res.writeHead(200, { ...h, "Content-Type": TYPES[".js"] }); return res.end("/* analytics stubbed by serve.mjs */"); }
  if (!fs.existsSync(f) || fs.statSync(f).isDirectory()) { res.writeHead(404, h); return res.end("404"); }
  let body = fs.readFileSync(f);
  if (f.endsWith(".html")) {
    let s = stripTrackers(body.toString());
    if (!u.searchParams.has("noprobe")) s = s.replace(/<head[^>]*>/i, (m) => m + PROBE);
    body = Buffer.from(s);
  }
  res.writeHead(200, { ...h, "Content-Type": TYPES[path.extname(f)] || "application/octet-stream" });
  res.end(body);
});
server.on("error", (e) => {
  if (e.code !== "EADDRINUSE" || PORT > 8890) { console.error(e.message); process.exit(1); }
  PORT++; LOG = logFor(PORT); server.listen(PORT);
});
server.on("listening", () => console.log(`serving ${ROOT} on http://localhost:${PORT} (analytics stubbed, no-store, probe on; log ${LOG})`));
server.listen(PORT);
