# Home IQ — Landing Pages Portfolio

Static HTML/CSS/JS landing pages for home-improvement lead-gen across 12 US verticals.

## Live navigation

Once deployed: `https://<deployment>.vercel.app/verticals/home-security/landings/INDEX.html`

## Tech stack

- Plain HTML5, CSS3 (inline `<style>`), vanilla JS
- Google Fonts (Inter)
- Mobile-first
- No build step — every page is self-contained and viewable via plain HTTP

## Structure

```
.
├── CLAUDE.md                     # Project context for Claude (work modes, tone)
├── _templates/                   # Reusable templates (landing, brief, reference)
├── _playbook/                    # Universal copy principles
└── verticals/
    └── [slug]/
        ├── brief.md              # Vertical-specific audience and messaging
        ├── references/           # Competitor inspo
        └── landings/
            ├── INDEX.html        # Navigation page for all versions
            ├── INSIGHTS.md       # Design rules / lessons learned
            ├── CHANGELOG.md
            ├── _shared/          # Privacy, Terms, Contact
            └── v{N}-{name}/      # One self-contained landing per folder
                ├── index.html
                └── images/
```

## Current focus

`verticals/home-security/landings/` — 13 versions iteratively built:
- **v1 family**: original live pages extracted
- **v2/v3**: brand-neutral + vivint CSS override experiments
- **v4 family** (teal): 6 variants — 3 photo options × 3 hero approaches (side, fullbleed, split, card)
- **v5 family** (blue): 3 variants — different hero photos with Vivint blue palette

See `verticals/home-security/landings/INSIGHTS.md` for design rules and lessons learned.

## Local dev

```bash
cd verticals/home-security/landings
python -m http.server 8090
```

Open `http://localhost:8090/INDEX.html`.

## Deployment

Vercel — static hosting. See `vercel.json`.
