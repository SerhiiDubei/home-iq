# Walk-In Shower — Landings Changelog

## Versioning Structure

```
landings/
├── INDEX.html             ← navigation between versions
├── INSIGHTS.md            ← principles & lessons (read before any task)
├── CHANGELOG.md           ← this file
├── baseline/              ← faithful rebuild of HomeQuotePro prelander (A/B control)
├── v1-trust-offer/        ← + trust & grounded offer & sticky CTA
├── v2-interactive-quiz/   ← step-by-step quiz with progress bar (vanilla JS)
└── v3-visual-proof/       ← before/after slider + benefits + 1-day badge
```

All versions are self-contained (inline CSS+JS, Google Fonts Rubik, no Convertri/CDN deps).
All CTAs point to the funnel: `homeimprove.io/get-quotes/walk-in-shower/`.
Approach across all 4 is identical (quiz prelander) — each variant moves ONE lever.

---

## baseline — May 2026

Faithful rebuild of competitor `homeimprove.io/article/walk-in-shower/home-quote-pro/`
(see `../references/home-quote-pro.md`). Rebranded HomeQuotePro → Home IQ, softened the
"not part of Google/META" disclaimer, fixed headline typos. Same content, flow and look,
in our stack (semantic HTML + BEM CSS + extracted design tokens). Serves as the A/B control.

## v1-trust-offer — May 2026

**Lever: trust + offer.** Per copy-principles #1 (grounded offer), #4 (real urgency), #6 (authority).

| Area | baseline | v1 |
|------|----------|----|
| Offer | "save thousands" (vague) | "Up to $1,500 Off + Free In-Home Design Consultation" |
| Urgency | none | "2026 enrollment — limited installer slots in your area" |
| Social proof header | none | 4.9★ / 12,000+ homeowners bar |
| Authority | none | A+ BBB · 4.9★ Google · Licensed in 48 states |
| Mobile CTA | inline only | sticky bottom CTA |

## v2-interactive-quiz — May 2026

**Lever: interaction.** The 3 static questions become a step-by-step quiz with a progress
bar (goal-gradient effect). Vanilla JS, no deps.
- All-YES → "qualified" celebration screen → funnel.
- Any NO → softer "you may still have options" screen → funnel.
- `decideOutcome()` (≈line 242) is the **qualification routing rule** — DEFAULT = strict (all 3 YES).

## v3-visual-proof — May 2026

**Lever: visual credibility.** Adds the missing visual proof for a visual purchase.
- Interactive before/after slider (clip-path + range input, vanilla JS).
- "Installed in as little as 1 day" badge (brief differentiator).
- 4 benefits with parallel structure (copy-principle #5): Installed in 1 Day / Built for Easy Access / Made to Stay Clean / Backed for Life.

---

## Pending (PM)
- [ ] v2: confirm `decideOutcome()` rule (strict vs loose) — depends on how the funnel pays per lead.
- [ ] Replace hero/before-after placeholders with real photos (local `images/` per version).
- [ ] Confirm offer numbers ($1,500, lifetime warranty, 48 states) are approved/compliant.
- [ ] Add `_shared/` (privacy, terms) if these go live standalone.
