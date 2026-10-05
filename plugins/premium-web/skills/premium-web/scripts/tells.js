// Templaty-tells scanner. Paste into a devtools / claude-in-chrome javascript_tool, or run headless:
//   EVAL=scripts/tells.js SHOTS=0 node scripts/chrome-shot.mjs <url> <out> 1440   (result in report.json -> eval)
//   Apps / tools people operate (dashboards, admin, consoles, run views): MODE=app (alias: tool). chrome-shot sets window.__TELLS_MODE and window.__TELLS_CLASS
//   (the step 0 classification from NOTES.md, scripts/classify.py); in devtools set both before pasting: window.__TELLS_MODE = "app"; window.__TELLS_CLASS = { mode: "app", density_target: 20 }.
//   Without __TELLS_CLASS the scan refuses (UNVERIFIED). Default mode is "marketing" and its behaviour is unchanged. The app profile and its thresholds table are in
//   references/wow.md "App mode"; this file's TH.app is the machine copy (test_tells.js asserts they agree).
// Returns JSON: each tell with a count, examples, and hit=true when over its threshold. Thresholds were set on
// 2026-10-01 against Angel's verdicts: ember + meridian REJECTED, pebble + halcyon APPROVED (see rubric.md).
// Heuristics, not proof: a hit means "the critic must look at this", a clean scan does not mean premium.
// NOT RUN != PASS. Result carries mode and desktop_gates (false when the viewport is < 1000px wide: the desktop gates (marketing: type_scale, wow_visible,
// scale_change; app: density, page_shaped_mismatch) are then NOT evaluated; scan at 1440). Callers must treat a missing result, an exception, a missing desktop_gates
// or {error:"UNVERIFIED: ..."} as UNVERIFIED (critic.py exits 3; chrome-shot.mjs exits 1 on craft_fail). Under node
// (`node -e "require('./scripts/tells.js')"`) it only exports { TH, appGates, appExempt } for scripts/test_tells.js.
(() => {
  // Gate numbers. marketing: documented here only for reference, the inline gates below are unchanged (wow_visible 25% x 30%,
  // type_scale 4x, scale_change >= 2 below the hero). app: references/wow.md "App mode" table (a test keeps the two in step).
  const TH = { marketing: { wow_w: 0.25, wow_h: 0.3, ratio: 4, breaks: 2 },
               app: { fields: 24, tap: 24, small_frac: 0.1, states: 3, state_chars: 8, hero_px: 56, scroll_vh: 3, tall_sec: 0.6, shell_vh: 1.15, bleed_vh: 2 } };
  const STATES = ["empty", "loading", "error", "partial"];
  // App profile, pure scoring from measurements m (the DOM block below produces them; test_tells.js drives this with synthetic ones).
  //  density: items visible in the first 1440x900 viewport >= the density_target stated in NOTES.md (screens with no list declare data-screen="form|detail|editor" and need >= TH.app.fields data points instead).
  //  interactive_affordance: 0 pointer-looking or role-ed non-native controls without focus, 0 controls without an accessible name, <= max(2, 10%) controls under 24px.
  //  state_coverage: >= 3 of empty/loading/error/partial present (data-state hooks, aria-busy, [data-skeleton]) with real message text (>= 8 chars; loading may be a skeleton).
  //  page_shaped_mismatch: >= 2 of {hero, scroll_sections, no_shell, closing_cta}, or no persistent shell on a page taller than 2 viewports. It flags WRONG-MODE STRUCTURE.
  //  data_wow_in_app: any [data-wow] (that attribute only feeds the marketing wow_visible gate; on an app screen it is detector nudging).
  const appGates = (m, T = TH.app) => {
    const desk = m.vw >= 1000, list = !m.formScreen, got = list ? m.rows : m.fields, need = list ? m.target : T.fields;
    const sig = { hero: !!m.hero, scroll_sections: m.tallSections >= 3 && m.docVh >= T.scroll_vh, no_shell: !m.shell, closing_cta: !!m.closing };
    const n = Object.values(sig).filter(Boolean).length, hits = Object.keys(sig).filter((k) => sig[k]);
    const st = STATES.filter((k) => m.states.includes(k));
    return {
      density: { measured: got, need, basis: list ? "rows" : "fields", hit: desk && (!m.target && list ? true : got < need),
        reason: !m.target && list ? "UNVERIFIED: no density_target in the step 0 classification" : got < need ? `${got} ${list ? "rows" : "data points"} visible at 1440x900, target ${need}` : "" },
      interactive_affordance: { controls: m.controls, unfocusable: m.fake, nameless: m.nameless, under_min: m.small, hit: m.fake > 0 || m.nameless > 0 || m.small > Math.max(2, m.controls * T.small_frac) },
      state_coverage: { present: st, missing: STATES.filter((k) => !st.includes(k)), hit: st.length < T.states },
      page_shaped_mismatch: { signals: hits, hit: desk && (n >= 2 || (sig.no_shell && m.docVh > T.bleed_vh)),
        reason: n >= 2 || (sig.no_shell && m.docVh > T.bleed_vh) ? "this screen is shaped like a marketing page (" + hits.join(", ") + "): the gate is flagging the WRONG-MODE STRUCTURE, not a taste problem. If the product is only read, re-run step 0 as READ (marketing); if people operate it, rebuild as a persistent shell + nav with the work surface in the first viewport" : "" },
      data_wow_in_app: { count: m.dataWow, hit: m.dataWow > 0, reason: m.dataWow ? "data-wow is the marketing wow marker; app mode has no wow gate, so this only nudges a detector (remove it)" : "" },
    };
  };
  // Mode-aware exemptions (app mode ONLY; marketing returns false/unchanged). A tool UI legitimately repeats data cells, lists steps
  // beside a log, and colours only state (app-exemplars: 90 identical bars per row, 1-3 hues for state). Heuristics with a stated ceiling:
  //  grid: >= 6 equal cells (repeated data) or compact cells <= 72px tall (status/KPI cells); 3-5 tall equal cards still fire.
  //  split: a list of >= 6 items is data (steps, runs), not a decorative 3-5 item timeline.
  //  palette: one state hue is the norm; only an app with NO hue at all (and no drawn media) is one-note.
  const appExempt = { grid: (mode, n, cellH) => mode === "app" && (n >= 6 || cellH <= 72), split: (mode, items) => mode === "app" && items >= 6,
                      paletteHit: (mode, hues, below) => (mode === "app" ? hues === 0 : hues <= 1) && below < 2 };
  if (typeof document === "undefined") { if (typeof module !== "undefined") module.exports = { TH, appGates, appExempt }; return; }
  const MODE = window.__TELLS_MODE === "tool" ? "app" : window.__TELLS_MODE || "marketing"; // tool is the old name of app
  if (MODE !== "marketing" && MODE !== "app") return { error: "UNVERIFIED: unknown tells mode " + JSON.stringify(MODE) + " (use marketing or app)" };
  const CLS = window.__TELLS_CLASS;
  if (!CLS || (CLS.mode === "tool" ? "app" : CLS.mode) !== MODE) return { error: "UNVERIFIED: no step 0 classification for mode " + MODE + " (window.__TELLS_CLASS; chrome-shot reads NOTES.md via scripts/classify.py, exit 4 if missing)" };
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
    if (same.length >= 3 && sameTag && !hasMedia && r0.width > 160 && !appExempt.grid(MODE, same.length, r0.height)) grids.push(name(p) + " x" + same.length);
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
  out.palette = { chromatic_hues: used.length, body_bg_lightness: +bgL.toFixed(2), hit: false }; // set below, once media is counted

  // 5. Material: raster/vector/canvas visuals >= 200px outside the first section (photo, render, illustration, WebGL).
  const media = [...document.querySelectorAll("img, canvas, video, svg, body *")].filter((m) => { const r = m.getBoundingClientRect();
    return vis(m) && r.width >= 200 && r.height >= 120 && (/^(IMG|CANVAS|VIDEO|svg)$/.test(m.tagName) || /url\(/.test(getComputedStyle(m).backgroundImage)); });
  const below = media.filter((m) => !sections[0] || !sections[0].contains(m));
  out.material = { media_total: media.length, below_hero: below.length, hit: below.length === 0 };
  // one-note = single accent hue AND (almost) no images/renders/canvas to carry colour and depth (halcyon: gold on black + film imagery passes)
  out.palette.hit = appExempt.paletteHit(MODE, used.length, below.length);

  // 6. Empty spacing: per section, share of a 16x10 sample grid covered by a text line, media, or a coloured box.
  const cover = sections.map((s) => { const sr = s.getBoundingClientRect(), sbg = getComputedStyle(s).backgroundColor;
    const rects = [...s.querySelectorAll("*")].filter((e) => { if (!vis(e)) return false; const cs = getComputedStyle(e);
      return /^(IMG|CANVAS|VIDEO|svg|PRE|INPUT|TEXTAREA|BUTTON|TABLE)$/i.test(e.tagName) || (cs.backgroundColor !== "rgba(0, 0, 0, 0)" && cs.backgroundColor !== sbg) || cs.backgroundImage !== "none"
        || [...e.childNodes].some((c) => c.nodeType === 3 && c.textContent.trim()); }).map((e) => e.getBoundingClientRect());
    let hitN = 0; for (let i = 0.5; i < 16; i++) for (let j = 0.5; j < 10; j++) { const x = sr.left + (sr.width * i) / 16, y = sr.top + (sr.height * j) / 10;
      if (rects.some((r) => x >= r.left && x <= r.right && y >= r.top && y <= r.bottom)) hitN++; }
    return { section: name(s), coverage: +(hitN / 160).toFixed(2) }; });
  const sparse = cover.filter((c) => c.coverage < 0.3);
  out.empty_spacing = { per_section: cover, sparse: sparse.map((c) => c.section), hit: sparse.length >= Math.max(2, sections.length * 0.4) };

  // 8. Category cliches (dev tools especially).
  const text = document.body.innerText;
  const cl = [/curl\s+-[a-zA-Z]*\s+\S+\s*\|\s*(sh|bash)/, /no daemon/i, /no telemetry|zero telemetry/i, /blazing(ly)? fast/i, /zero[- ]config/i, /supercharge/i, /seamless(ly)?/i, /10x/i, /built for (developers|teams)/i, /all-in-one/i].filter((r) => r.test(text)).map(String);
  out.cliches = { found: cl, hit: cl.length >= 2 };

  // 9. Monospace-everything: body copy set in a monospace face.
  const ps = [...document.querySelectorAll("main p")].filter(vis), mono = ps.filter((p) => /mono|courier|menlo|consolas/i.test(getComputedStyle(p).fontFamily));
  out.mono_body = { share: ps.length ? +(mono.length / ps.length).toFixed(2) : 0, hit: ps.length > 3 && mono.length / ps.length > 0.6 };

  // 10. Bordered mono panels as the default container (ember r2: "terminal card" in every section).
  const isMono = (e) => /mono|courier|menlo|consolas/i.test(getComputedStyle(e).fontFamily);
  const panel = (e) => { const cs = getComputedStyle(e), r = e.getBoundingClientRect(); if (okMark(e) || !vis(e) || r.width < 160 || r.height < 60) return false;
    const boxed = parseFloat(cs.borderTopWidth) > 0 && parseFloat(cs.borderLeftWidth) > 0 || (cs.backgroundColor !== "rgba(0, 0, 0, 0)" && cs.backgroundColor !== getComputedStyle(e.parentElement).backgroundColor);
    if (!boxed) return false; const t = [...e.querySelectorAll("*")].filter((c) => [...c.childNodes].some((n) => n.nodeType === 3 && n.textContent.trim()));
    const own = (c) => [...c.childNodes].reduce((a, n) => a + (n.nodeType === 3 ? n.textContent.trim().length : 0), 0); // own text only, no double counting
    const all = t.reduce((a, c) => a + own(c), 0) || 1, m = t.filter(isMono).reduce((a, c) => a + own(c), 0);
    return (t.length ? m / all : isMono(e) ? 1 : 0) > 0.3; }; // a command panel with prose around it still counts (ember r2 revisions panel: 34% mono at 1440)
  const panelSecs = sections.filter((sec) => [...sec.querySelectorAll("div, pre, figure, article, aside, section, ol, ul")].some(panel));
  out.mono_panels = { sections_with_panel: panelSecs.length, hit: sections.length >= 3 && panelSecs.length / sections.length >= 0.6 };

  // 11. Timeline list beside a mono command panel (ember r2 revisions: "looks bad").
  const split = sections.filter((sec) => { const lists = [...sec.querySelectorAll("ol, ul")].filter((l) => vis(l) && l.children.length >= 3 && !l.closest("nav") && !appExempt.split(MODE, l.children.length));
    const panels = [...sec.querySelectorAll("pre, div, figure")].filter(panel);
    return lists.some((l) => { const a = l.getBoundingClientRect(); return panels.some((p) => { if (p.contains(l) || l.contains(p)) return false; const b = p.getBoundingClientRect();
      return Math.min(a.bottom, b.bottom) - Math.max(a.top, b.top) > Math.min(a.height, b.height) * 0.4 && (b.left >= a.right - 4 || a.left >= b.right - 4); }); }); });
  out.timeline_code_split = { sections: split.map(name), hit: split.length >= 1 };

  // 12. No full-bleed moment below the hero (required alternative: one full-bleed typographic or drawn section).
  const vw = document.documentElement.clientWidth, fb = sections.slice(1).some((sec) => [sec, ...sec.querySelectorAll("*")].some((e) => { if (!vis(e)) return false; const r = e.getBoundingClientRect(), cs = getComputedStyle(e);
    const drawn = /^(IMG|CANVAS|VIDEO|svg)$/i.test(e.tagName) || cs.backgroundImage.includes("url(") || (e !== sec && cs.backgroundColor !== "rgba(0, 0, 0, 0)" && cs.backgroundColor !== getComputedStyle(sec).backgroundColor);
    const bigType = parseFloat(cs.fontSize) >= Math.min(160, vw * 0.16) && [...e.childNodes].some((n) => n.nodeType === 3 && n.textContent.trim());
    return (drawn && r.width >= vw * 0.95 && r.height >= Math.min(innerHeight * 0.4, 360)) || (bigType && r.width >= vw * 0.6); }) || (sec !== sections[0] && getComputedStyle(sec).backgroundColor !== getComputedStyle(document.body).backgroundColor && sec.getBoundingClientRect().width >= vw * 0.95 && ([...sec.querySelectorAll("img, canvas, svg, video")].some((m) => vis(m) && m.getBoundingClientRect().width >= vw * 0.6)
      // or display type on a contrasting full-width ground (sealref transcript: 316px numerals on paper went undetected)
      || [...sec.querySelectorAll("*")].some((t) => vis(t) && parseFloat(getComputedStyle(t).fontSize) >= Math.min(160, vw * 0.16) && [...t.childNodes].some((n) => n.nodeType === 3 && n.textContent.trim())))));
  out.no_fullbleed = { hit: sections.length >= 3 && !fb };

  // 13. Saturated fields (Angel on ember v3: "oversaturated, feels like a game / toy"): share of each section's sample grid
  // covered by a HOT background (HSV S > .72, V > .5: primaries, neon, brand pink). Calibrated 2026-10-02 with
  // scripts/saturation.py: approved pebble/halcyon/tracer 0.00-0.01 of screenshot area, rejected ember v3 0.19, ember v2 0.14.
  const hot = (c) => { const v = rgb(c); if (v.length < 3 || v[3] === 0) return false; const mx = Math.max(v[0], v[1], v[2]), mn = Math.min(v[0], v[1], v[2]); return mx / 255 > 0.5 && mx > 0 && (mx - mn) / mx > 0.72; };
  const hotShare = sections.map((sec) => { const sr = sec.getBoundingClientRect();
    const rects = [sec, ...sec.querySelectorAll("*")].filter((e) => vis(e) && hot(getComputedStyle(e).backgroundColor)).map((e) => e.getBoundingClientRect());
    let n = 0; for (let i = 0.5; i < 16; i++) for (let j = 0.5; j < 10; j++) { const x = sr.left + (sr.width * i) / 16, y = sr.top + (sr.height * j) / 10; if (rects.some((r) => x >= r.left && x <= r.right && y >= r.top && y <= r.bottom)) n++; }
    return { section: name(sec), hot: +(n / 160).toFixed(2) }; });
  const toy = hotShare.filter((c) => c.hot > 0.25);
  out.saturated_fields = { per_section: hotShare, toy: toy.map((c) => c.section), hit: toy.length >= 2 || (sections.length > 0 && hotShare.reduce((a, c) => a + c.hot, 0) / sections.length > 0.15) };

  // 14. Section-craft gates (2026-10-04, fixmap redesign: "looks better but basic, no wow"). HARD gates (craft_fail), not just tells.
  // panel_run: >3 CONSECUTIVE sections whose main content is a bordered/filled box (any font), i.e. the dev-tool panel template.
  const boxed = (e) => { const cs = getComputedStyle(e), r = e.getBoundingClientRect(); if (okMark(e) || !vis(e) || r.width < 240 || r.height < 80 || /^(BUTTON|A|INPUT|LABEL|TD|TH|TR|LI)$/.test(e.tagName) || e.querySelector("img, picture, canvas, video")) return false; // rendered material inside = not a bare panel (pebble clay cards)
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
  // wow_visible (marketing): a canvas/svg/video/img >= 25% of viewport width and >= 30% of viewport height must start inside the first viewport (the wow is above the fold). (Comment said 50% x 40% until 2026-10-05; the code was always 25% x 30%, wow.md agrees with the code. Tool mode enforces 50% x 40%.)
  const first = [...document.querySelectorAll("canvas, svg, img, video, picture, [data-wow], section, header, div")].some((e) => { if (!vis(e)) return false; const r = e.getBoundingClientRect(), cs = getComputedStyle(e); const media = /^(CANVAS|SVG|IMG|VIDEO|PICTURE)$/i.test(e.tagName) || e.hasAttribute("data-wow") || cs.backgroundImage.includes("url("); return media && r.width >= vw * 0.25 && r.height >= innerHeight * 0.3 && r.top < innerHeight * 0.75 && r.top + scrollY >= 0 && r.top + scrollY < innerHeight; });
  out.wow_visible = { hit: vw >= 1000 && !first }; // desktop only; 390 is judged from the critic frames
  let craftKeys = ["panel_run", "scale_change", "type_scale", "wow_visible"];
  if (MODE === "app") {
    // App profile (references/wow.md "App mode"). Not hard-gated here: type_scale, wow_visible, scale_change, panel_run (measured, kept visible as hit:false) and the page-rhythm
    // detectors empty_spacing, no_fullbleed, mono_panels (they score a scrolling page's sections, which is the marketing shape; they no longer count toward the 4+ rule).
    // Kept: equal_card_grids, caps_micro_labels, palette (hard, in craft_fail) and material (a counted tell). Added hard gates (all in craft_fail): see appGates.
    for (const k of [...craftKeys, "empty_spacing", "no_fullbleed", "mono_panels"]) { out[k].measured_hit = out[k].hit; out[k].hit = false; out[k].gated = false; }
    const T = TH.app, vh = innerHeight, docH = document.documentElement.scrollHeight, inView = (e) => { const r = e.getBoundingClientRect(); return r.bottom > 0 && r.top < vh && r.right > 0 && r.left < vw; };
    const NAVQ = "nav, [role=navigation], [role=tablist], [role=toolbar], [role=menubar], aside", INTQ = "a[href], button, [role=tab], [role=menuitem], [role=link], [role=button]";
    // density: the largest group of >= 3 sibling rows (table rows, list items, role=row/listitem/option/treeitem, [data-row]) and how many sit in the first viewport
    const groups = new Map();
    document.querySelectorAll("tbody tr, [role=row], li, [role=listitem], [role=option], [role=treeitem], [data-row], [data-item]").forEach((e) => { if (vis(e) && !e.closest("nav, [role=navigation], [role=menu], [role=tablist]") && !e.querySelector("[role=columnheader]")) groups.set(e.parentElement, [...(groups.get(e.parentElement) || []), e]); });
    const rows = Math.max(0, ...[...groups.values()].filter((g) => g.length >= 3).map((g) => g.filter(inView).length));
    const leaf = [...document.querySelectorAll("body *")].filter((e) => vis(e) && inView(e) && (/^(INPUT|SELECT|TEXTAREA)$/.test(e.tagName) || [...e.childNodes].some((n) => n.nodeType === 3 && n.textContent.trim())));
    const screenKind = ((document.querySelector("main") || document.body).getAttribute("data-screen") || document.body.getAttribute("data-screen") || "").toLowerCase();
    // interactive affordance
    const NATIVE = /^(A|BUTTON|INPUT|SELECT|TEXTAREA|SUMMARY|LABEL|OPTION)$/, ROLES = /^(button|link|tab|menuitem|switch|checkbox|radio|option|treeitem|combobox|slider)$/;
    const ctl = [...document.querySelectorAll("a[href], button, input:not([type=hidden]), select, textarea, summary, [role], [tabindex]")].filter((e) => vis(e) && !e.disabled && (NATIVE.test(e.tagName) || ROLES.test(e.getAttribute("role") || "") || e.hasAttribute("tabindex")));
    const fake = [...document.querySelectorAll("body *")].filter((e) => vis(e) && !NATIVE.test(e.tagName) && !e.closest("a[href], button, [tabindex], label, summary") && !e.querySelector("a[href], button, input, select, textarea, [tabindex]")
      && ((getComputedStyle(e).cursor === "pointer" && [...e.childNodes].some((n) => n.nodeType === 3 && n.textContent.trim())) || (ROLES.test(e.getAttribute("role") || "") && !e.hasAttribute("tabindex")))).length;
    const named = (e) => !!(e.getAttribute("aria-label") || e.getAttribute("aria-labelledby") || e.getAttribute("title") || (e.labels && e.labels.length) || (e.textContent || "").trim() || (e.tagName === "INPUT" && /^(button|submit|reset)$/.test(e.type) && e.value));
    const nameless = ctl.filter((e) => !named(e)).length;
    const small = ctl.filter((e) => { const r = e.getBoundingClientRect(); return !(e.tagName === "A" && getComputedStyle(e).display === "inline") && !(e.tagName === "INPUT" && /^(checkbox|radio)$/.test(e.type) && e.labels && e.labels.length) && Math.min(r.width, r.height) < T.tap; }).length;
    // state coverage: hooks only count with a real message (a template's content, or the element's own text); loading may be a skeleton / aria-busy
    const states = new Set(); document.querySelectorAll("[data-state], [aria-busy=true], [data-skeleton]").forEach((e) => { const txt = ((e.content ? e.content.textContent : e.textContent) || "").trim();
      for (const k of (e.getAttribute("data-state") || "").toLowerCase().split(/\s+/)) if (STATES.includes(k) && (txt.length >= T.state_chars || k === "loading")) states.add(k);
      if (e.matches("[aria-busy=true], [data-skeleton]")) states.add("loading"); });
    // page shape signals
    const bigH1 = [...document.querySelectorAll("h1")].some((h) => vis(h) && parseFloat(getComputedStyle(h).fontSize) >= T.hero_px), heroEl = [...document.querySelectorAll("[class*=hero i], [data-hero]")].some((e) => vis(e) && e.getBoundingClientRect().height >= vh * 0.4);
    const tallSections = sections.filter((e) => e.getBoundingClientRect().height >= vh * T.tall_sec).length;
    const shells = [...document.querySelectorAll(NAVQ)].filter((e) => vis(e) && e.querySelectorAll(INTQ).length >= 2);
    const persistent = (e) => { for (let p = e; p && p !== document.documentElement; p = p.parentElement) if (/^(fixed|sticky)$/.test(getComputedStyle(p).position)) return true; return false; };
    const shell = shells.some((e) => persistent(e) || docH <= vh * T.shell_vh);
    const tail = [...sections.slice(-2), ...document.querySelectorAll("footer")].map((e) => e.innerText || "").join("\n");
    const footCols = [...document.querySelectorAll("footer")].some((f) => [...f.querySelectorAll("div, ul, nav")].filter((c) => c.querySelectorAll("a").length >= 3).length >= 3);
    const closing = /\b(get started|start (free|your|building)|book a demo|request a demo|contact sales|sign up (free|today)|join (the|our)|ready to|try it free|subscribe to)\b/i.test(tail) || footCols;
    Object.assign(out, appGates({ vw, rows, fields: leaf.length, target: CLS.density_target || 0, formScreen: /^(form|detail|editor|settings)$/.test(screenKind),
      controls: ctl.length, fake, nameless, small, states: [...states], hero: bigH1 || heroEl, tallSections, docVh: +(docH / vh).toFixed(2), shell, closing,
      dataWow: document.querySelectorAll("[data-wow]").length + (document.documentElement.hasAttribute("data-wow") ? 1 : 0) }));
    craftKeys = ["density", "interactive_affordance", "state_coverage", "page_shaped_mismatch", "data_wow_in_app", "equal_card_grids", "caps_micro_labels", "palette"]; // each kept tell is a hard fail here (material stays a counted tell: a table-only tool has no drawn field)
  }
  const craft_fail = craftKeys.filter((k) => out[k].hit);

  const hits = Object.entries(out).filter(([k, v]) => v.hit && !craftKeys.includes(k)).map(([k]) => k);
  // Calibration: see references/rubric.md "Templaty tells" (pinned rejected pages >= 4, approved pages <= 3).
  // So: >= 4 hits = templaty (fail), 3 = look hard, <= 2 = no structural tells (still needs the visual critic).
  return { mode: MODE, desktop_gates: vw >= 1000, sections: sections.length, hits, templaty: hits.length >= 4, craft_fail, tells: out };
})();
