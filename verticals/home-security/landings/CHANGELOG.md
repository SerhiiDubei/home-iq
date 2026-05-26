# Home Security — Landings Changelog

## Versioning Structure

```
landings/
├── v1-upgrade-security/    ← Live page: homeimprove.io/article/home-security/upgrade-your-security/
├── v1-install-direct/      ← Live page: homeimprove.io/article/home-security/security-install-direct/
├── v2-improved/            ← Our improved brand-neutral landing
└── CHANGELOG.md
```

---

## v2-improved — May 2026

**Based on competitor research (Vivint, ADT, Ring, Frontpoint, Cove)**

### What changed vs v1

| Area | v1 (live) | v2 (improved) |
|------|-----------|---------------|
| **Hero offer** | Generic | "Up to 6 Months Free Monitoring + Free HD Camera" (Vivint-style) |
| **Trust bar** | None | 5 signals: BBB A+, Licensed Pros, Free Estimates, No Obligation, 4.8★ Google |
| **Benefits block** | None | 6-card grid with parallel structure |
| **Awards / Trust** | None | Newsweek · PCMag · NerdWallet · BBB with quotes (ADT-style) |
| **Reviews** | None | 3 verified reviews |
| **FAQ** | None | 5 questions with accordion |
| **Phone CTA** | None | Sticky phone button (IP-based zip checker placeholder) |
| **Offer banner** | Promo code "4FREE" | Event-anchored: Memorial Day Sale |

### Pending (Vladyslav)
- [ ] Replace `(800) 555-0000` with actual buyer phone number
- [ ] Implement IP → zip checker (`fetch('https://ipapi.co/json/')`)
- [ ] Connect form submit to buyer API endpoint

---

## v1-install-direct — original

Live URL: `homeimprove.io/article/home-security/security-install-direct/`
Promo: Vivint-branded, promo code `4FREE` (free installation)
Extracted: May 2026

---

## v1-upgrade-security — original

Live URL: `homeimprove.io/article/home-security/upgrade-your-security/`
Style: Generic home security, Swiper slider, CDN assets at `homeimprove.b-cdn.net`
Extracted: May 2026
