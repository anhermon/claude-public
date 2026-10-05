// Self-check for tells.js tool mode: node scripts/test_tells.js  (no browser, no deps; synthetic measurements)
const assert = require("assert"), fs = require("fs"), path = require("path");
const { TH, toolGates } = require("./tells.js");
const vw = 1440, good = { vw, hero: { w: 0.58, h: 0.62, top: 0.13, marks: 30 }, big: 96, median: 13, breaks: 1 };
const keys = (m) => Object.entries(toolGates(m)).filter(([, v]) => v.hit).map(([k]) => k).sort();
assert.deepStrictEqual(keys(good), []);                                                    // a real data-object tool passes
assert.deepStrictEqual(keys({ ...good, hero: null }), ["wow_visible"]);                    // no declared data object
assert.deepStrictEqual(keys({ ...good, hero: { ...good.hero, w: 0.49 } }), ["wow_visible"]); // just under 50% wide
assert.deepStrictEqual(keys({ ...good, hero: { ...good.hero, h: 0.39 } }), ["wow_visible"]);
assert.deepStrictEqual(keys({ ...good, hero: { ...good.hero, marks: 11 } }), ["wow_visible"]); // a sketch, not records
assert.deepStrictEqual(keys({ ...good, hero: { ...good.hero, top: 1.2 } }), ["wow_visible"]);  // below the fold
assert.deepStrictEqual(keys({ ...good, big: 32, median: 13 }), ["type_scale"]);             // generic KPI numeral: 2.5x
assert.deepStrictEqual(keys({ ...good, big: 56, median: 13 }), ["type_scale"]);             // 4.3x but < 4vw (57.6px)
assert.deepStrictEqual(keys({ ...good, big: 58, median: 13 }), []);
assert.deepStrictEqual(keys({ ...good, breaks: 0 }), ["scale_change"]);
assert.deepStrictEqual(keys({ ...good, vw: 390, hero: null, breaks: 0, big: 20 }), []);     // desktop-only gates (desktop_gates:false tells callers)
assert.deepStrictEqual(keys({ ...good, hero: { ...good.hero, marks: 0, listy: true } }), ['wow_visible']); // data-wow on a table (listy hero, no drawn shapes)
// the generic stand-in mockup: no data-wow, 24px KPI numerals, no bleed => all three fail
assert.deepStrictEqual(keys({ vw, hero: null, big: 24, median: 14, breaks: 0 }), ["scale_change", "type_scale", "wow_visible"]);
// single source of truth: wow.md's machine line must equal TH.tool
const line = fs.readFileSync(path.join(__dirname, "../references/wow.md"), "utf8").match(/tool-mode-numbers[^\n]*?: ([^>]*?) -->/)[1];
const doc = Object.fromEntries(line.split(/\s+/).map((kv) => kv.split("=")).map(([k, v]) => [k, +v]));
assert.deepStrictEqual(doc, TH.tool);
// marketing numbers are untouched
assert.deepStrictEqual(TH.marketing, { wow_w: 0.25, wow_h: 0.3, ratio: 4, breaks: 2 });
const src = fs.readFileSync(path.join(__dirname, "tells.js"), "utf8"); // ...and TH.marketing really is what the inline gates enforce
for (const lit of ["r.width >= vw * 0.25 && r.height >= innerHeight * 0.3", "big / body < 4", "scaleSecs.length < 2"]) assert(src.includes(lit), "marketing gate literal moved: " + lit);
console.log("test_tells ok");
