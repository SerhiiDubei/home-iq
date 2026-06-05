# Reference: HomeQuotePro — Walk-In Shower Quiz Prelander

## Source
- URL: https://homeimprove.io/article/walk-in-shower/home-quote-pro/
- Type: competitor (paid-traffic prelander / advertorial)
- Date added: 2026-05-29
- Raw capture: `home-quote-pro-raw.html`, `hqp-style.css`, `hqp-inline-styles.css` (this folder)

## Format
Quiz-style **prelander** built on Convertri. Not a full landing — its only job is to
warm up cold paid traffic (FB/Google) and hand the lead to the quote funnel at
`homeimprove.io/get-quotes/walk-in-shower/`. Minimal: text + colored buttons, no real photos.

### Structure (top → bottom)
1. Headline — "Homeowners Get Huge Relief Remodelling Their Bathrooms With New 2026 Services..."
2. Hero block (color/empty)
3. Big YES button → funnel
4. Disclaimer ("not part of Google/META... bathrooms are not free...")
5. YES / NO buttons → funnel
6. 3 qualifying questions: Homeowner? / Home over 5 yrs? / Live in USA?
7. 5× five-star testimonials (name + city)
8. Closing question: "Do You Meet These 3 Simple Requirements to Qualify...?"

## Design tokens (extracted from their CSS)
- Font: **Rubik** (400/500/600/700)
- CTA / link blue: `#2563eb` → hover `#1745aa`
- YES green: `#04ae15` · NO red: `#eb060a`
- Headings: `#111827` · Body: `#374151` · Disclaimer plate: `#afbff8` (~15% alpha)
- Radius: 8px buttons, 15px cards

## What Works
- **Quiz qualification = micro-commitment ladder.** 3 trivial YES clicks build inertia before the ask.
- **Binary YES/NO only.** Zero typing, zero friction — perfect for cold mobile traffic.
- **Social proof heavy** — 5 testimonials with name + city reads as real.
- **"2026" + "new services"** = freshness/urgency framing.
- Single conversion target (the funnel) repeated 4×.

## What Doesn't Work
- **Aggressive / low-trust framing** — "not part of Google/META" disclaimer signals spam.
- **No grounded offer** — "save thousands" with no number, no reason (violates copy-principle #1 & #2).
- **No real visuals** — no before/after, no product photo for a highly visual purchase.
- **Questions are fake** — every answer (YES and NO) goes to the same funnel; no real routing.
- Typos in headline ("Remodelling", "Savings Homeowners").

## Key Takeaways
1. **Keep the quiz-prelander approach** — it's the right format for this traffic. Improve the levers, not the model.
2. **Ground the offer** — replace "save thousands" with a specific number + reason + condition.
3. **Add visual proof** — before/after is decisive for a visual remodel purchase (see v3).

## Our adaptations
Rebuilt clean (Home IQ brand, our stack) as `landings/baseline/` + 3 improvement variants.
See `landings/CHANGELOG.md` and `landings/INSIGHTS.md`.
