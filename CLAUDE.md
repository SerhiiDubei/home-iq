# Home IQ — Project Context for Claude

## What is Home IQ
A product portfolio of home improvement landing pages targeting US homeowners.
Each vertical is an independent lead-gen or informational landing page.
PM: product owner responsible for strategy, copy direction, UX, and feature rollout.

## My Role in This Project
- Build new landing pages (HTML/CSS/JS)
- Improve existing landings (CRO, UX, copy, features)
- Generate and refine marketing copy
- Curate references and competitive analysis per vertical
- Integrate new features into existing landings

---

## Verticals Index

| Slug | Vertical | Status |
|------|----------|--------|
| `home-security` | Home Security | Active |
| `roofing` | Roofing | Active |
| `flooring` | Flooring | Active |
| `siding` | Siding | Active |
| `hvac` | HVAC | Active |
| `walk-in-shower` | Walk-in Shower | Active |
| `solar` | Solar | Active |
| `gutters` | Gutters | Active |
| `kitchen` | Kitchen Remodeling | Active |
| `plumbing` | Plumbing | Active |
| `home-warranty` | Home Warranty | Active |
| `walk-in-tubs` | Walk-in Tubs | Active |
| `pest-control` | Pest Control | Active |

Each vertical lives in its own folder: `verticals/[slug]/`

---

## Work Modes

When I start a task, I should identify which mode applies:

### COPY mode
Generating or editing marketing copy: headlines, subheads, body text, CTAs, bullet points.
- Match tone: trustworthy, direct, US homeowner audience
- Focus on benefits over features
- CTA language: action-oriented ("Get Free Quote", "See Your Options", "Check Availability")
- Read `verticals/[slug]/brief.md` for vertical-specific tone and audience

### DESIGN mode
Creating or restructuring landing page layout and UX.
- Tech stack: plain HTML5, CSS3, vanilla JS (no frameworks unless specified)
- Mobile-first approach
- Sections to consider: Hero, Trust signals, Benefits, How it works, CTA, FAQ, Footer
- Reference `_templates/landing-template.html` as baseline

### FEATURE mode
Adding or improving specific features on existing landings.
- Preserve existing styles and structure
- Features: forms, modals, step flows, quiz/calculator, chat widgets, sticky headers
- Test for mobile breakpoints

### REFERENCE mode
Collecting and organizing competitive intel and inspiration.
- Store in `verticals/[slug]/references/`
- Use `_templates/reference-template.md` format
- Note: competitor URL, what works, what doesn't, visual notes

---

## Technical Standards

- HTML: semantic tags, accessible markup (aria labels on forms)
- CSS: BEM-like naming, no inline styles except dynamic JS
- JS: vanilla only unless specified, no jQuery
- Images: use descriptive alt text, optimize for web
- Forms: all lead forms need name, phone, zip as minimum fields

---

## Tone of Voice

**Audience:** US homeowners, age 35–65, practical, value-conscious
**Tone:** Trustworthy, knowledgeable, no-pressure
**Avoid:** jargon, aggressive sales language, empty superlatives
**Use:** specific numbers, social proof, local relevance signals

---

## How to Start Each Task

1. Identify the vertical (check verticals index)
2. Read `verticals/[slug]/brief.md` for context
3. **Read `_playbook/copy-principles.md`** — universal rules for all copy and offers
4. Identify the work mode (COPY / DESIGN / FEATURE / REFERENCE)
5. Check `verticals/[slug]/landings/` for existing files before creating new ones
6. Follow technical standards above
