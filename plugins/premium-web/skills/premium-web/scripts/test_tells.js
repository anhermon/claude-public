// Self-check for tells.js: node scripts/test_tells.js  (no browser, no deps; synthetic measurements). Live DOM checks: scripts/test_app_live.sh
const assert = require("assert"), fs = require("fs"), path = require("path");
const { TH, appGates, appExempt } = require("./tells.js");
const vw = 1440;
const good = { vw, rows: 30, fields: 0, target: 20, formScreen: false, controls: 35, fake: 0, nameless: 0, small: 0, states: ["empty", "loading", "error", "partial"],
  hero: false, tallSections: 0, docVh: 1, shell: true, closing: false, dataWow: 0 };
const keys = (m) => Object.entries(appGates(m)).filter(([, v]) => v.hit).map(([k]) => k).sort();
assert.deepStrictEqual(keys(good), []);                                                                      // a real work screen passes
// density: rows visible vs the stated target
assert.deepStrictEqual(keys({ ...good, rows: 19 }), ["density"]);                                             // 19 < 20
assert.deepStrictEqual(keys({ ...good, rows: 20 }), []);
assert.deepStrictEqual(keys({ ...good, target: 0 }), ["density"]);                                            // no stated target = UNVERIFIED (hit), never a pass
assert(/UNVERIFIED/.test(appGates({ ...good, target: 0 }).density.reason));
assert.deepStrictEqual(keys({ ...good, vw: 390, rows: 2 }), []);                                              // desktop-only
assert.deepStrictEqual(keys({ ...good, formScreen: true, rows: 0, fields: TH.app.fields }), []);              // data-screen=form: data points instead of rows
assert.deepStrictEqual(keys({ ...good, formScreen: true, rows: 0, fields: TH.app.fields - 1 }), ["density"]);
// interactive affordance: zero tolerance for fake/nameless, 10% for small targets
assert.deepStrictEqual(keys({ ...good, fake: 1 }), ["interactive_affordance"]);                               // pointer-looking div with no focus
assert.deepStrictEqual(keys({ ...good, nameless: 1 }), ["interactive_affordance"]);                           // icon button without a name
assert.deepStrictEqual(keys({ ...good, small: 3 }), []);                                                      // 3 of 35 < max(2, 3.5)
assert.deepStrictEqual(keys({ ...good, small: 4 }), ["interactive_affordance"]);
assert.deepStrictEqual(keys({ ...good, vw: 390, fake: 1 }), ["interactive_affordance"]);                       // not desktop-only
// state coverage: >= 3 of 4
assert.deepStrictEqual(keys({ ...good, states: ["empty", "error", "loading"] }), []);
assert.deepStrictEqual(keys({ ...good, states: ["empty", "error"] }), ["state_coverage"]);
assert.deepStrictEqual(keys({ ...good, states: [] }), ["state_coverage"]);
// page shape: >= 2 of hero / scroll sections / no shell / closing CTA, or no shell on a tall page; the message names the wrong-mode structure
assert.deepStrictEqual(keys({ ...good, hero: true, tallSections: 4, docVh: 5, shell: false }), ["page_shaped_mismatch"]);   // the skeleton landing page
assert.deepStrictEqual(keys({ ...good, hero: true, closing: true }), ["page_shaped_mismatch"]);
assert.deepStrictEqual(keys({ ...good, hero: true }), []);                                                    // one signal alone is not enough
assert.deepStrictEqual(keys({ ...good, shell: false, docVh: 1 }), []);                                        // single screen without nav: one signal
assert.deepStrictEqual(keys({ ...good, shell: false, docVh: 2.5 }), ["page_shaped_mismatch"]);                // scrolling page without a shell
assert(/WRONG-MODE STRUCTURE/.test(appGates({ ...good, hero: true, closing: true }).page_shaped_mismatch.reason));
assert.deepStrictEqual(keys({ ...good, vw: 390, hero: true, closing: true }), []);                            // desktop-only
// data-wow on an app screen is detector nudging
assert.deepStrictEqual(keys({ ...good, dataWow: 1 }), ["data_wow_in_app"]);
// the old tool-mode wow numbers are gone: no size/type/bleed gate exists in the app profile
for (const k of ["wow_w", "wow_h", "marks", "display_vw", "ratio", "breaks"]) assert(!(k in TH.app), "app profile must not gate " + k);
// single source of truth: wow.md's machine line must equal TH.app
const line = fs.readFileSync(path.join(__dirname, "../references/wow.md"), "utf8").match(/app-mode-numbers[^\n]*?: ([^>]*?) -->/)[1];
const doc = Object.fromEntries(line.split(/\s+/).map((kv) => kv.split("=")).map(([k, v]) => [k, +v]));
assert.deepStrictEqual(doc, TH.app);
// marketing numbers are untouched
assert.deepStrictEqual(TH.marketing, { wow_w: 0.25, wow_h: 0.3, ratio: 4, breaks: 2 });
const src = fs.readFileSync(path.join(__dirname, "tells.js"), "utf8"); // ...and TH.marketing really is what the inline gates enforce
for (const lit of ["r.width >= vw * 0.25 && r.height >= innerHeight * 0.3", "big / body < 4", "scaleSecs.length < 2"]) assert(src.includes(lit), "marketing gate literal moved: " + lit);
// marketing still fires on the structure the app profile exempts / does not know about
assert(src.includes('out.wow_visible = { hit: vw >= 1000 && !first }') && src.includes('out.type_scale = { ratio: +(big / body).toFixed(1), hit: vw >= 1000 && big / body < 4 }'));
assert(src.includes('let craftKeys = ["panel_run", "scale_change", "type_scale", "wow_visible"]'));          // marketing hard-fail list unchanged
assert(src.indexOf("appGates({") > src.indexOf('if (MODE === "app")'));                                       // app measurements only run in the app branch
// the app profile is classification-gated: tells refuses without window.__TELLS_CLASS
assert(src.includes("__TELLS_CLASS") && src.includes("UNVERIFIED: no step 0 classification"));
// mode-aware tells: app exempts repeated data cells / data lists / state-only palette; marketing still fires on the same input
assert(appExempt.grid("app", 90, 20) && appExempt.grid("app", 6, 200) && appExempt.grid("app", 4, 60));       // status bars, repeated rows, compact KPI cells
assert(!appExempt.grid("app", 4, 120) && !appExempt.grid("app", 3, 200));                                     // tall equal cards (KPI tiles / feature cards) still fire in app mode
assert(!appExempt.grid("marketing", 90, 20) && !appExempt.grid("marketing", 6, 200) && !appExempt.grid("marketing", 4, 60)); // marketing: never exempt
assert(!appExempt.grid("tool", 90, 20));                                                                      // the old name is normalised before it reaches here, never exempts by itself
assert(appExempt.split("app", 52) && appExempt.split("app", 6) && !appExempt.split("app", 5));
assert(!appExempt.split("marketing", 52) && !appExempt.split("marketing", 6));
assert(appExempt.paletteHit("marketing", 1, 0) && appExempt.paletteHit("marketing", 0, 1) && !appExempt.paletteHit("marketing", 2, 0)); // marketing one-note unchanged
assert(!appExempt.paletteHit("app", 1, 0) && !appExempt.paletteHit("app", 3, 0) && appExempt.paletteHit("app", 0, 0));
assert(!appExempt.paletteHit("marketing", 1, 2) && !appExempt.paletteHit("app", 0, 2));
console.log("test_tells ok");
