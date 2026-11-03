// Templaty-tells scanner. Paste into a devtools / claude-in-chrome javascript_tool, or run headless:
//   EVAL=scripts/tells.js SHOTS=0 node scripts/chrome-shot.mjs <url> <out> 1440   (result in report.json -> eval)
// Returns JSON: each tell with a count, examples, and hit=true when over its threshold. Thresholds were set on
// 2026-10 on a small labelled set (rejected builds hit 5-9 tells, approved builds 2-4); see references/section-craft.md.
// Heuristics, not proof: a hit means "the critic must look at this", a clean scan does not mean premium.
(() => {
  const vis = (e) => { const r = e.getBoundingClientRect(), s = getComputedStyle(e); return r.width > 0 && r.height > 0 && s.visibility !== "hidden" && s.display !== "none" && +s.opacity > 0; };
  const sections = [...document.querySelectorAll("main > section, main > div > section, body > section")].filter(vis);
  const name = (e) => e.id || e.getAttribute("aria-labelledby") || e.className.toString().slice(0, 20) || e.tagName;
  const rgb = (c) => (c.match(/[\d.]+/g) || []).map(Number);
  const hue = ([r, g, b]) => { r /= 255; g /= 255; b /= 255; const mx = Math.max(r, g, b), mn = Math.min(r, g, b), d = mx - mn; if (d < 0.12) return null;
    const h = mx === r ? ((g - b) / d) % 6 : mx === g ? (b - r) / d + 2 : (r - g) / d + 4; return Math.round(((h * 60) + 360) % 360 / 30); }; // 12 hue buckets
  const out = {};
  // data-tell-ok on an element (or an ancestor) marks a DELIBERATE repeated component (three registered sheets, table rows,
  // a version strip): equal_card_grids and mono_panels skip it. Use sparingly and say why in a comment; the critic still looks.
  const okMark = (e) => !!e.closest("[data-tell-ok]");

  // 1. Equal card grids: >=3 siblings, same size (+-6px), each with a border or its own background.
  const grids = [];
  document.querySelectorAll("body *").forEach((p) => {
    if (okMark(p)) return; const kids = [...p.children].filter(vis); if (kids.length < 3) return;
    const boxed = kids.filter((k) => { const s = getComputedStyle(k); return parseFloat(s.borderTopWidth) > 0 || parseFloat(s.borderLeftWidth) > 0 || (s.backgroundColor !== "rgba(0, 0, 0, 0)" && s.backgroundColor !== getComputedStyle(p).backgroundColor) || s.boxShadow !== "none"; });
    if (boxed.length < 3) return;
    const r0 = boxed[0].getBoundingClientRect();
    const same = boxed.filter((k) => { const r = k.getBoundingClientRect(); return Math.abs(r.width - r0.width) < 6 && Math.abs(r.height - r0.height) < 6; });
    const sameTag = same.every((k) => k.children.length === same[0].children.length);
    const hasMedia = same.some((k) => k.querySelector("img, picture, canvas, video, svg *:nth-child(6)"));
    if (same.length >= 3 && sameTag && !hasMedia && r0.width > 160) grids.push(name(p) + " x" + same.length);
  });
  out.equal_card_grids = { count: grids.length, examples: grids.slice(0, 5), hit: grids.length >= 1 };

  // 2. ALL-CAPS tracked micro-labels: small (<=13px) uppercase text with letter-spacing >= .04em.
  const caps = [...document.querySelectorAll("body *")].filter((e) => {
    if (!vis(e) || ![...e.childNodes].some((n) => n.nodeType === 3 && n.textContent.trim().length > 1)) return false;
    const s = getComputedStyle(e), fs = parseFloat(s.fontSize), ls = parseFloat(s.letterSpacing) || 0, t = e.textContent.trim();
    return fs <= 13.5 && (s.textTransform === "uppercase" || (t === t.toUpperCase() && /[A-Z]{3}/.test(t))) && ls / fs >= 0.04;
  });
  const perSec = sections.map((s) => caps.filter((c) => s.contains(c)).length);
  out.caps_micro_labels = { count: caps.length, per_section: perSec, examples: caps.slice(0, 6).map((e) => e.textContent.trim().slice(0, 30)),
    hit: caps.length > 12 || perSec.filter((n) => n >= 2).length >= Math.max(3, sections.length * 0.5) };

  // 3. Bracketed nav gimmick: [how] [config]
  const nav = [...document.querySelectorAll("nav a, header a")].filter(vis);
  const br = nav.filter((a) => /^\s*[\[<{(]/.test(a.textContent) || /[\[<{]/.test(getComputedStyle(a, "::before").content));
  out.bracket_nav = { count: br.length, hit: br.length >= 2 };

  // 4. One-note palette: chromatic hue buckets used by visible text, backgrounds and borders (area-weighted bg).
  const hues = new Map();
  document.querySelectorAll("body, body *").forEach((e) => { if (!vis(e)) return; const s = getComputedStyle(e), r = e.getBoundingClientRect();
    for (const [c, w] of [[s.backgroundColor, r.width * r.height], [s.color, e.childNodes.length ? 200 : 0], [s.borderTopColor, parseFloat(s.borderTopWidth) ? r.width : 0]]) {
      const v = rgb(c); if (v.length < 3 || v[3] === 0 || !w) continue; const h = hue(v); if (h !== null) hues.set(h, (hues.get(h) || 0) + w); } });
  const total = [...hues.values()].reduce((a, b) => a + b, 0) || 1, used = [...hues.entries()].filter(([, w]) => w / total > 0.04);
  const bgL = (() => { const v = rgb(getComputedStyle(document.body).backgroundColor); return v.length ? (v[0] + v[1] + v[2]) / 765 : 1; })();
  out.palette = { chromatic_hues: used.length, body_bg_lightness: +bgL.toFixed(2), hit: used.length <= 1 }; // revised below

  // 5. Material: raster/vector/canvas visuals >= 200px outside the first section (photo, render, illustration, WebGL).
  const media = [...document.querySelectorAll("img, canvas, video, svg, body *")].filter((m) => { const r = m.getBoundingClientRect();
    return vis(m) && r.width >= 200 && r.height >= 120 && (/^(IMG|CANVAS|VIDEO|svg)$/.test(m.tagName) || /url\(/.test(getComputedStyle(m).backgroundImage)); });
  const below = media.filter((m) => !sections[0] || !sections[0].contains(m));
  out.material = { media_total: media.length, below_hero: below.length, hit: below.length === 0 };
  // one-note = single accent hue AND (almost) no images/renders/canvas to carry colour and depth (gold on black with film imagery passes)
  out.palette.hit = out.palette.hit && below.length < 2;

  // 6. Empty spacing: per section, share of a 16x10 sample grid covered by a text line, media, or a coloured box.
  const cover = sections.map((s) => { const sr = s.getBoundingClientRect(), sbg = getComputedStyle(s).backgroundColor;
    const rects = [...s.querySelectorAll("*")].filter((e) => { if (!vis(e)) return false; const cs = getComputedStyle(e);
      return /^(IMG|CANVAS|VIDEO|svg|PRE|INPUT|TEXTAREA|BUTTON|TABLE)$/i.test(e.tagName) || (cs.backgroundColor !== "rgba(0, 0, 0, 0)" && cs.backgroundColor !== sbg) || cs.backgroundImage !== "none"
        || [...e.childNodes].some((c) => c.nodeType === 3 && c.textContent.trim()); }).map((e) => e.getBoundingClientRect());
    let hitN = 0; for (let i = 0.5; i < 16; i++) for (let j = 0.5; j < 10; j++) { const x = sr.left + (sr.width * i) / 16, y = sr.top + (sr.height * j) / 10;
      if (rects.some((r) => x >= r.left && x <= r.right && y >= r.top && y <= r.bottom)) hitN++; }
    return { section: name(s), coverage: +(hitN / 160).toFixed(2) }; });
  // A persistent subject (fixed/sticky canvas or [data-subject]) behind the sections IS the content of the "empty" area: count it as full coverage.
  const persistentSubject = [...document.querySelectorAll("canvas, [data-subject], [data-gl]")].some((e) => { const cs = getComputedStyle(e), r = e.getBoundingClientRect(); const pinned = (n) => { for (; n && n !== document.body; n = n.parentElement) { const p = getComputedStyle(n).position; if (p === "fixed" || p === "sticky") return true; } return false; }; return vis(e) && (pinned(e) || e.hasAttribute("data-subject")) && r.width >= innerWidth * 0.5 && r.height >= innerHeight * 0.5; });
  const sparse = persistentSubject ? [] : cover.filter((c) => c.coverage < 0.3);
  out.empty_spacing = { per_section: cover, sparse: sparse.map((c) => c.section), persistentSubject, hit: sparse.length >= Math.max(2, sections.length * 0.4) };

  // 8. Category cliches (dev tools especially).
  const text = document.body.innerText;
  const cl = [/curl\s+-[a-zA-Z]*\s+\S+\s*\|\s*(sh|bash)/, /no daemon/i, /no telemetry|zero telemetry/i, /blazing(ly)? fast/i, /zero[- ]config/i, /supercharge/i, /seamless(ly)?/i, /10x/i, /built for (developers|teams)/i, /all-in-one/i].filter((r) => r.test(text)).map(String);
  out.cliches = { found: cl, hit: cl.length >= 2 };

  // 9. Monospace-everything: body copy set in a monospace face.
  const ps = [...document.querySelectorAll("main p")].filter(vis), mono = ps.filter((p) => /mono|courier|menlo|consolas/i.test(getComputedStyle(p).fontFamily));
  out.mono_body = { share: ps.length ? +(mono.length / ps.length).toFixed(2) : 0, hit: ps.length > 3 && mono.length / ps.length > 0.6 };

  // 10. Bordered mono panels as the default container (a "terminal card" in every section).
  const isMono = (e) => /mono|courier|menlo|consolas/i.test(getComputedStyle(e).fontFamily);
  const panel = (e) => { const cs = getComputedStyle(e), r = e.getBoundingClientRect(); if (okMark(e) || !vis(e) || r.width < 160 || r.height < 60) return false;
    const boxed = parseFloat(cs.borderTopWidth) > 0 && parseFloat(cs.borderLeftWidth) > 0 || (cs.backgroundColor !== "rgba(0, 0, 0, 0)" && cs.backgroundColor !== getComputedStyle(e.parentElement).backgroundColor);
    if (!boxed) return false; const t = [...e.querySelectorAll("*")].filter((c) => [...c.childNodes].some((n) => n.nodeType === 3 && n.textContent.trim()));
    const own = (c) => [...c.childNodes].reduce((a, n) => a + (n.nodeType === 3 ? n.textContent.trim().length : 0), 0); // own text only, no double counting
    const all = t.reduce((a, c) => a + own(c), 0) || 1, m = t.filter(isMono).reduce((a, c) => a + own(c), 0);
    return (t.length ? m / all : isMono(e) ? 1 : 0) > 0.3; }; // a command panel with prose around it still counts (34% mono at 1440 was enough)
  const panelSecs = sections.filter((sec) => [...sec.querySelectorAll("div, pre, figure, article, aside, section, ol, ul")].some(panel));
  out.mono_panels = { sections_with_panel: panelSecs.length, hit: sections.length >= 3 && panelSecs.length / sections.length >= 0.6 };

  // 11. Timeline list beside a mono command panel.
  const split = sections.filter((sec) => { const lists = [...sec.querySelectorAll("ol, ul")].filter((l) => vis(l) && l.children.length >= 3 && !l.closest("nav"));
    const panels = [...sec.querySelectorAll("pre, div, figure")].filter(panel);
    return lists.some((l) => { const a = l.getBoundingClientRect(); return panels.some((p) => { if (p.contains(l) || l.contains(p)) return false; const b = p.getBoundingClientRect();
      return Math.min(a.bottom, b.bottom) - Math.max(a.top, b.top) > Math.min(a.height, b.height) * 0.4 && (b.left >= a.right - 4 || a.left >= b.right - 4); }); }); });
  out.timeline_code_split = { sections: split.map(name), hit: split.length >= 1 };

  // 12. No full-bleed moment below the hero (required alternative: one full-bleed typographic or drawn section).
  const vw = document.documentElement.clientWidth, fb = sections.slice(1).some((sec) => [sec, ...sec.querySelectorAll("*")].some((e) => { if (!vis(e)) return false; const r = e.getBoundingClientRect(), cs = getComputedStyle(e);
    const drawn = /^(IMG|CANVAS|VIDEO|svg)$/i.test(e.tagName) || cs.backgroundImage.includes("url(") || (e !== sec && cs.backgroundColor !== "rgba(0, 0, 0, 0)" && cs.backgroundColor !== getComputedStyle(sec).backgroundColor);
    const bigType = parseFloat(cs.fontSize) >= Math.min(160, vw * 0.16) && [...e.childNodes].some((n) => n.nodeType === 3 && n.textContent.trim());
    return (drawn && r.width >= vw * 0.95 && r.height >= Math.min(innerHeight * 0.4, 360)) || (bigType && r.width >= vw * 0.6); }) || (sec !== sections[0] && getComputedStyle(sec).backgroundColor !== getComputedStyle(document.body).backgroundColor && sec.getBoundingClientRect().width >= vw * 0.95 && ([...sec.querySelectorAll("img, canvas, svg, video")].some((m) => vis(m) && m.getBoundingClientRect().width >= vw * 0.6)
      // or display type on a contrasting full-width ground (316px numerals on paper went undetected)
      || [...sec.querySelectorAll("*")].some((t) => vis(t) && parseFloat(getComputedStyle(t).fontSize) >= Math.min(160, vw * 0.16) && [...t.childNodes].some((n) => n.nodeType === 3 && n.textContent.trim())))));
  out.no_fullbleed = { hit: sections.length >= 3 && !fb };

  // 13. Saturated fields (toy palette): share of each section's sample grid
  // covered by a HOT background (HSV S > .72, V > .5: primaries, neon, brand pink). Same thresholds and provenance as
  // scripts/saturation.py (approved pages 0.00-0.01 of screenshot area, rejected toy palettes 0.14-0.19).
  const hot = (c) => { const v = rgb(c); if (v.length < 3 || v[3] === 0) return false; const mx = Math.max(v[0], v[1], v[2]), mn = Math.min(v[0], v[1], v[2]); return mx / 255 > 0.5 && mx > 0 && (mx - mn) / mx > 0.72; };
  const hotShare = sections.map((sec) => { const sr = sec.getBoundingClientRect();
    const rects = [sec, ...sec.querySelectorAll("*")].filter((e) => vis(e) && hot(getComputedStyle(e).backgroundColor)).map((e) => e.getBoundingClientRect());
    let n = 0; for (let i = 0.5; i < 16; i++) for (let j = 0.5; j < 10; j++) { const x = sr.left + (sr.width * i) / 16, y = sr.top + (sr.height * j) / 10; if (rects.some((r) => x >= r.left && x <= r.right && y >= r.top && y <= r.bottom)) n++; }
    return { section: name(sec), hot: +(n / 160).toFixed(2) }; });
  const toy = hotShare.filter((c) => c.hot > 0.25);
  out.saturated_fields = { per_section: hotShare, toy: toy.map((c) => c.section), hit: toy.length >= 2 || (sections.length > 0 && hotShare.reduce((a, c) => a + c.hot, 0) / sections.length > 0.15) };

  // 14. Section-craft gates (a build passed type, palette and Lighthouse and was still "basic, no wow"). HARD gates (craft_fail), not just tells.
  // panel_run: >3 CONSECUTIVE sections whose main content is a bordered/filled box (any font), i.e. the dev-tool panel template.
  const boxed = (e) => { const cs = getComputedStyle(e), r = e.getBoundingClientRect(); if (okMark(e) || !vis(e) || r.width < 240 || r.height < 80 || /^(BUTTON|A|INPUT|LABEL|TD|TH|TR|LI)$/.test(e.tagName) || e.querySelector("img, picture, canvas, video")) return false; // rendered material inside = not a bare panel
    return (parseFloat(cs.borderTopWidth) > 0 && parseFloat(cs.borderLeftWidth) > 0) || (cs.backgroundColor !== "rgba(0, 0, 0, 0)" && cs.backgroundColor !== getComputedStyle(e.parentElement).backgroundColor); };
  const secBoxed = sections.map((sec) => { const sr = sec.getBoundingClientRect(); let a = 0; [...sec.querySelectorAll("div, pre, figure, article, aside, table, ul, ol")].filter(boxed).forEach((e) => { const r = e.getBoundingClientRect(); if (!e.parentElement.closest("[class]") || !boxed(e.parentElement)) a += r.width * r.height; }); return a / (sr.width * sr.height || 1) > 0.08; });
  let run = 0, maxRun = 0; secBoxed.forEach((b) => { run = b ? run + 1 : 0; maxRun = Math.max(maxRun, run); });
  out.panel_run = { max_consecutive: maxRun, hit: maxRun > 3 };
  // scale_change: >= 2 sections below the hero must break the column (a >=95%-viewport-wide drawn/typographic element, or a contrasting full-width ground, or type >= 12vw).
  const scaleSecs = sections.slice(1).filter((sec) => { const sc = getComputedStyle(sec), bc = getComputedStyle(document.body);
    const ground = sc.backgroundColor !== "rgba(0, 0, 0, 0)" && sc.backgroundColor !== bc.backgroundColor && sec.getBoundingClientRect().width >= vw * 0.95;
    const wide = [...sec.querySelectorAll("svg, canvas, img, video, div, figure")].some((e) => { if (!vis(e)) return false; const r = e.getBoundingClientRect(); const d = /^(IMG|CANVAS|VIDEO|svg)$/i.test(e.tagName) || getComputedStyle(e).backgroundImage !== "none"; return d && r.width >= vw * 0.95 && r.height >= 200; });
    const big = [...sec.querySelectorAll("*")].some((t) => vis(t) && parseFloat(getComputedStyle(t).fontSize) >= vw * 0.12 && [...t.childNodes].some((n) => n.nodeType === 3 && n.textContent.trim()));
    return ground || wide || big; });
  out.scale_change = { sections: scaleSecs.map(name), count: scaleSecs.length, hit: vw >= 1000 && sections.length >= 3 && scaleSecs.length < 2 };
  // type_scale: the display/body ratio of the page (largest visible text vs body). < 4x = flat scale.
  const fs = [...document.querySelectorAll("main *")].filter((t) => vis(t) && [...t.childNodes].some((n) => n.nodeType === 3 && n.textContent.trim())).map((t) => parseFloat(getComputedStyle(t).fontSize));
  const body = fs.sort((a, b) => a - b)[Math.floor(fs.length / 2)] || 16, big = Math.max(...fs, 0);
  out.type_scale = { ratio: +(big / body).toFixed(1), hit: vw >= 1000 && big / body < 4 }; // desktop only: 390 viewports compress display type
  // wow_visible: a canvas/svg/video/img >= 50% of viewport width and >= 40% of viewport height must start inside the first viewport (the wow is above the fold).
  const first = [...document.querySelectorAll("canvas, svg, img, video, picture, [data-wow], section, header, div")].some((e) => { if (!vis(e)) return false; const r = e.getBoundingClientRect(), cs = getComputedStyle(e); const media = /^(CANVAS|SVG|IMG|VIDEO|PICTURE)$/i.test(e.tagName) || e.hasAttribute("data-wow") || cs.backgroundImage.includes("url("); return media && r.width >= vw * 0.25 && r.height >= innerHeight * 0.3 && r.top < innerHeight * 0.75 && r.top + scrollY >= 0 && r.top + scrollY < innerHeight; });
  out.wow_visible = { hit: vw >= 1000 && !first }; // desktop only; 390 is judged from the critic frames
  // storefronts (references/direction.md): product cards carry [data-product]; a link from one to another origin sends the buyer away
  const outLinks = [...document.querySelectorAll("[data-product] a[href]")].filter((a) => a.origin && a.origin !== location.origin);
  out.product_links_out = { count: outLinks.length, examples: outLinks.slice(0, 3).map((a) => a.href), hit: outLinks.length > 0 };
  const craftKeys = ["panel_run", "scale_change", "type_scale", "wow_visible"];
  const craft_fail = craftKeys.filter((k) => out[k].hit);

  const hits = Object.entries(out).filter(([k, v]) => v.hit && !craftKeys.includes(k)).map(([k]) => k);
  // Calibration: see references/section-craft.md "Templaty tells" (rejected pages >= 4, approved pages <= 3).
  // So: >= 4 hits = templaty (fail), 3 = look hard, <= 2 = no structural tells (still needs the visual critic).
  return { sections: sections.length, hits, templaty: hits.length >= 4, craft_fail, tells: out };
})();
