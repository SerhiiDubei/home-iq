# Claude Design — Task Brief for v3-vivint-inspired

## What to paste into Claude Design

1. Open `claude.ai/design`
2. Start a new project
3. Paste the contents of `index-clean.html` (same folder as this file)
4. Then paste the prompt below

---

## Prompt to use in Claude Design

```
I have a home security lead-gen landing page that's styled to look like Vivint.com.

The page uses:
- Real Vivint design tokens: brand teal #05E5AF, black #000000, white text, Helvetica Neue font
- Structure copied from a live landing page (v1), with Vivint CSS applied on top via overrides
- CDN assets from homeimprove.b-cdn.net (images, base CSS)
- Swiper.js for portfolio slider

Please review this page and make the following improvements:

### Priority 1 — Visual polish
- Hero section: make sure the black background + hero image with teal CTA button looks clean and premium (like vivint.com/home-security)
- CTA button "GET FREE QUOTES →": should be teal #05E5AF with black text, bold, pill-shape or slightly rounded
- Trust bar icons (BBB Accredited, No Step Entry, Custom Tile, Grab Bars, Pro Install): update icon labels to match home security: replace "No Step Entry / Custom Tile / Grab Bars" with "24/7 Monitoring / Mobile App / Smart Alerts" — these are bathroom remodel icons mistakenly left from original template
- How It Works section (black background): ensure teal icon circles and white text are clearly readable

### Priority 2 — Copy improvements
- Hero headline: "Protect Your Home / Simple Security That Works" → keep or improve to feel more premium
- Form label "WHAT IS YOUR ZIP CODE?" → clean up to "Enter your ZIP code"
- CTA "GET FREE QUOTES →" → consider "Check Availability →" or keep current
- Trust bar items (hero__list): "✓ Free Estimates / ✓ Licensed Pros / ✓ No Obligation" — keep these, they're good

### Priority 3 — Section cleanup
- Portfolio section title "Finished Projects" → change to "Recently Installed Systems"
- Projects section "What's your home security project type?" → fine as-is
- Reviews section: avatars should be teal #05E5AF circles with initials in black

### Design tokens (DO NOT CHANGE THESE)
- Brand teal: #05E5AF
- Black (hero, How It Works, footer): #000000
- White backgrounds: #ffffff
- Light gray bg (portfolio, reviews): #f5f5f5
- All buttons: teal background, black text, font-weight: 500
- Font: "Helvetica Neue", Helvetica, Arial, sans-serif

### What NOT to change
- Overall page structure and sections (hero, portfolio, projects, how it works, benefits, reviews, FAQ, footer)
- CDN image URLs (they will load from homeimprove.b-cdn.net)
- Form action and links
- The JavaScript at the bottom (Swiper, accordion, modal)
```

---

## Context

- **Page type**: Lead-gen landing, US homeowners age 35-65
- **Goal**: User enters ZIP code → gets connected to home security installers
- **Style inspiration**: vivint.com — dark/black hero, mint teal CTAs, clean white sections
- **Base**: Copied from live page v1-upgrade-security, Vivint CSS applied as overrides
- **Live equivalent**: homeimprove.io/article/home-security/upgrade-your-security/
