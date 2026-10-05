// Benchmark measurement: computed styles of a live page. Synchronous expression, returns a JSON string.
// - claude-in-chrome: paste the whole file as the `text` of javascript_tool (action "javascript_exec") on the open tab.
// - headless batch:   EVAL=measure-site.js node chrome-shot.mjs <url> <out> 1440,390   (result lands in report.json)
// Short form: `SUMMARY=1 EVAL=scripts/measure-site.js ...` (chrome-shot sets window.__SUMMARY), or set window.__SUMMARY = true before
// pasting it: only palette, fonts, h1/h2/body, header, section heights (one compact JSON instead of ~60 lines; use it for reference sweeps).
// Each field: family | px size | weight | line-height ratio | tracking in em | text-transform.
// Read the result as data; cross-check big claims (e.g. "uses font X") against a screenshot.
(() => {
  const vis = (e) => { const r = e.getBoundingClientRect(), s = getComputedStyle(e); return r.width > 0 && r.height > 0 && s.visibility !== "hidden" && s.display !== "none" && +s.opacity > 0; };
  const own = (e) => [...e.childNodes].filter((n) => n.nodeType === 3).map((n) => n.textContent).join("").trim();
  const T = (e) => { if (!e) return null; const s = getComputedStyle(e), fs = parseFloat(s.fontSize);
    return `${s.fontFamily.split(",")[0].replace(/"/g, "")} | ${fs}px | ${s.fontWeight} | ${s.lineHeight === "normal" ? "normal" : (parseFloat(s.lineHeight) / fs).toFixed(2)} | ${s.letterSpacing === "normal" ? 0 : (parseFloat(s.letterSpacing) / fs).toFixed(3)}em | ${s.textTransform}`; };
  const first = (sel, f = () => true) => [...document.querySelectorAll(sel)].find((e) => vis(e) && f(e));
  const texts = [...document.querySelectorAll("body *")].filter((e) => own(e).length > 2 && vis(e));
  // character-weighted histogram: what the page is actually set in
  const hist = {};
  for (const e of texts) { const s = getComputedStyle(e); const k = `${s.fontFamily.split(",")[0].replace(/"/g, "")} ${parseFloat(s.fontSize)}px w${s.fontWeight}`; hist[k] = (hist[k] || 0) + own(e).length; }
  const biggest = texts.slice().sort((a, b) => parseFloat(getComputedStyle(b).fontSize) - parseFloat(getComputedStyle(a).fontSize))[0];
  const eyebrows = texts.filter((e) => { const s = getComputedStyle(e); return s.textTransform === "uppercase" && parseFloat(s.fontSize) <= 14; }).length;
  const header = [...document.querySelectorAll("header, nav, [role=banner]")].filter(vis).map((e) => e.getBoundingClientRect()).filter((r) => r.top < 60 && r.width > innerWidth * 0.6).map((r) => Math.round(r.height))[0];
  const btns = [...document.querySelectorAll("a, button")].filter((e) => { if (!vis(e)) return false; const s = getComputedStyle(e), r = e.getBoundingClientRect();
    return (s.backgroundColor !== "rgba(0, 0, 0, 0)" || parseFloat(s.borderTopWidth) > 0) && e.innerText.trim().length > 2 && r.height < 70 && r.height > 20; })
    .slice(0, 4).map((e) => { const s = getComputedStyle(e), r = e.getBoundingClientRect(); return `"${e.innerText.trim().slice(0, 18)}" ${Math.round(r.height)}h r${s.borderRadius} ${parseFloat(s.fontSize)}/${s.fontWeight} bg ${s.backgroundColor}`; });
  const pw = [...document.querySelectorAll("p")].filter((e) => vis(e) && e.innerText.length > 80).slice(0, 5).map((e) => Math.round(e.getBoundingClientRect().width));
  const secs = [...document.querySelectorAll("main > section, section")].filter(vis).slice(0, 6).map((e) => { const s = getComputedStyle(e); return parseFloat(s.paddingTop) + "/" + parseFloat(s.paddingBottom); });
  const trans = {}; for (const e of document.querySelectorAll("a, button")) { const s = getComputedStyle(e); if (s.transitionDuration !== "0s") { const k = s.transitionDuration.split(",")[0] + " " + s.transitionTimingFunction.match(/^[^,(]*(\([^)]*\))?/)[0]; trans[k] = (trans[k] || 0) + 1; } }
  const fonts = [...new Set([...document.fonts].filter((f) => f.status === "loaded").map((f) => f.family.replace(/"/g, "")))];
  const out = {
    url: location.host + location.pathname, viewport: innerWidth, bg: getComputedStyle(document.body).backgroundColor, color: getComputedStyle(document.body).color,
    webfonts_loaded: fonts.slice(0, 6), h1: T(first("h1")), h2: T(first("h2")), h3: T(first("h3")), biggest_text: T(biggest),
    body: T(first("p", (e) => e.innerText.length > 80)), nav_link: T(first("header a, nav a", (e) => e.innerText.trim().length > 2)), code: T(first("code, pre")),
    header_h: header, buttons: btns, paragraph_widths: pw, section_padding: secs, uppercase_small_labels: eyebrows,
    transitions: Object.entries(trans).sort((a, b) => b[1] - a[1]).slice(0, 3).map((x) => x[0]),
    top_text_styles: Object.entries(hist).sort((a, b) => b[1] - a[1]).slice(0, 5).map((x) => x[0] + " (" + x[1] + " chars)"),
  };
  if (window.__SUMMARY) { // short form: what you tabulate when comparing 6-12 reference sites
    const sec = [...document.querySelectorAll("main > section, section")].filter(vis).slice(0, 10).map((e) => Math.round(e.getBoundingClientRect().height));
    const pal = {}; for (const e of document.querySelectorAll("body, main > *, section, header, footer, a, button")) { if (!vis(e)) continue; const c = getComputedStyle(e).backgroundColor; if (c !== "rgba(0, 0, 0, 0)") pal[c] = (pal[c] || 0) + 1; }
    return JSON.stringify({ url: out.url, bg: out.bg, color: out.color, palette: Object.entries(pal).sort((a, b) => b[1] - a[1]).slice(0, 5).map((x) => x[0]), fonts: out.webfonts_loaded, h1: out.h1, h2: out.h2, body: out.body, header_h: out.header_h, section_heights: sec, section_padding: out.section_padding.slice(0, 3) });
  }
  return JSON.stringify(out, null, 1);
})()
