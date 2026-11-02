# Trust devices and lead capture (no dark patterns)

Countermeasure for F7 (failure-modes.md).

- **Proof inventory first** (spec-before-code.md section 2): list what is real and checkable: repos, releases,
  licences, dated stars, public talks, named clients who agreed to be named. The page may use only those items.
- **Never fabricate**: no invented stats, testimonials, logos, user counts, benchmarks or press. Sample data is
  labelled "sample data" where it appears. Visuals that are not measurements carry an "illustrative" caption.
- **Unverified claims are fabricated claims.** Every number has a source and a date next to it. Check claim wording
  against the product facts (a durability claim is true only for the materials it was verified for).
- **Specificity test** for each headline and claim: swap in a competitor's name. If it is still true and still
  reads the same, rewrite it with a fact only this product has.
- **Limits stated plainly** are a trust device: a "what it does not do" section, or a short limit note per proof
  item quoting the source.
- **Who replies**: a real name and how fast; "replies personally" only if true.
- **Lead capture**: one primary action repeated (hero, after proof, footer). No exit-intent popups, no fake
  scarcity or countdowns, no pre-ticked boxes, no confirmshaming, no forced account.
- **Analytics**: say so in the privacy line. Tests never send events to real analytics (`serve.mjs` stubs trackers,
  `chrome-shot.mjs` blocks them).
- **Concepts for fictional products** carry a small persistent "Concept, fictional product, sample data" tag in the
  nav (not a fixed overlay that covers content on phones).
- **Showcase and wrapper pages** (portfolio, directory, showcase) get an identity of their own; they must not inherit
  the author's own site styling. Check: put the wrapper's hero beside the author's own site; if one could be
  mistaken for the other, it fails.
- **Storefronts**: product links stay on site (a quick view or detail panel with image, material, dimensions, lead
  time, options, one next action); generated scenes are labelled as illustration; copy claims are checked per
  product.
