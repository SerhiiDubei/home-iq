# ТЗ — Playable Ad "Thief's POV"
## Meta Story Format | 1080×1920px | Vertical: Home Security

---

## 1. КОНЦЕПТ

Гравець — злодій. Нічна вулиця, 4 будинки. Треба обрати ціль.
Кожен будинок має різні сигнали безпеки. Після вибору — результат + освітній інсайт + CTA.

**Ключова ідея:** гравець на власному досвіді дізнається що камери працюють як DETERRENT (відлякують), а не тільки як запис.

---

## 2. GAME FLOW

```
[ЕКРАН 1] INTRO          ~2 сек    автоматично
[ЕКРАН 2] STREET SCENE   ~10 сек   інтерактивний (tap)
[ЕКРАН 3] OUTCOME        ~3 сек    анімація результату
[ЕКРАН 4] STAT REVEAL    ~2 сек    автоматично
[ЕКРАН 5] CTA SCREEN     ∞         чекає тапу
```

**Загальна тривалість до CTA:** ~17–20 сек

---

## 3. ЕКРАНИ ДЕТАЛЬНО

### ЕКРАН 1 — INTRO (2 сек)

**Візуал:**
- Чорний фон → fade in темно-синій ніч
- Силует злодія в капюшоні знизу екрана
- Текст з'являється зверху вниз:

```
"2:14 AM"           ← маленький, верхній центр, монospace шрифт
"You're the thief." ← великий, центр
"Pick your target." ← середній, під ним, з курсором що блимає
```

**Анімація:** текст — typewriter effect через GSAP, силует — slide up знизу

---

### ЕКРАН 2 — STREET SCENE (інтерактивний)

**Візуал:**
- Нічне небо (градієнт #0A0A1E → #1A1A3E)
- Місяць + 2–3 зірки (static)
- Вулиця — темно-сіра смуга внизу
- Ліхтар посередині (жовте світло, cone effect)
- 4 будинки горизонтально, рівні, з підписами A / B / C / D

**Будинки:**

| Будинок | Сигнали | Результат |
|---------|---------|-----------|
| **A** | Камера над дверима + security sign на газоні + floodlight | CAUGHT — тривога |
| **B** | Темно, без камери, без знака | "SUCCESS" → потім pivot до страху |
| **C** | Камера є але дивиться не туди (вбік) | CAUGHT — камера все одно спрацювала |
| **D** | Світло в вікні + motion sensor light | STARTLED — сусід викликав поліцію |

**UX механіка:**
- При hover/touch on house → легкий glow ефект (жовтий outline)
- Tap → house збільшується (scale 1.05) → transition до OUTCOME

**Підказка:** після 4 сек без дії — легке "pulse" анімація на будинку B (найлегша ціль) щоб підштовхнути гравця

---

### ЕКРАН 3 — OUTCOME

**House A (CAUGHT):**
```
Анімація: red flash по екрану → handcuffs іконка зверху вниз
Звук: немає (Meta muted by default)
Текст: "BUSTED."
Subtext: "The camera caught you before you touched the door."
```

**House B (VULNERABLE — "success"):**
```
Анімація: зелений flash → силует заходить у двері
Текст: "You got in."
Subtext: "No cameras. Easy target. Just like thousands of homes near you."
Колір тексту: спочатку зелений → через 1 сек fade до червоного
```

**House C (CAUGHT — wrong angle):**
```
Анімація: red flash → камера "повертається" і дивиться на злодія
Текст: "BUSTED."
Subtext: "Even a poorly placed camera triggered the alert."
```

**House D (STARTLED):**
```
Анімація: жовтий спалах від motion light → силует тікає
Текст: "Too risky."
Subtext: "Motion sensors. You ran. Someone called 911."
```

---

### ЕКРАН 4 — STAT REVEAL (2 сек)

**Для всіх outcomes (однаковий):**

```
Великий текст по центру:

"83%"                    ← величезний, білий, pop-in анімація

"of burglars skip homes  ← менший текст під ним
with visible cameras"

Source: Rutgers University Study  ← дрібний, знизу, курсив
```

**Анімація:** число "83%" — counter animation від 0 до 83 через GSAP

---

### ЕКРАН 5 — CTA SCREEN

**Візуал:**
- Темний фон (не чорний — #0F1923)
- Будинок з камерою (та сама іконка що в house A) — центр, великий
- Зелене світло над камерою = "захищено"

**Текст:**
```
"Make Your Home    ← великий, білий
the Wrong Target"

[GET FREE QUOTE →] ← кнопка, яскраво-зелена #22C55E, rounded
```

**Sub-trust line під кнопкою:**
```
"Free consultation · No commitment · 48-state coverage"
```

**Meta інтеграція:**
```javascript
document.querySelector('#cta-btn').addEventListener('click', () => {
  FbPlayableAd.onCTAClick()
})
```

---

## 4. ТЕХНІЧНИЙ СТЕК

| Компонент | Рішення | Розмір |
|-----------|---------|--------|
| Рендеринг | PixiJS 7.x | ~500KB |
| Анімації | GSAP 3.x | ~70KB |
| Ассети | Inline SVG | ~50KB |
| Ігровий код | Vanilla JS | ~20KB |
| **Разом** | | **~640KB** |

Запас до ліміту Meta 2MB: **~1.36MB**

---

## 5. АССЕТИ (всі inline SVG)

| Ассет | Опис |
|-------|------|
| `thief` | Силует в капюшоні, вид збоку |
| `house-base` | Базовий будинок (однаковий для всіх) |
| `camera-icon` | Камера на стіні |
| `camera-wrong` | Камера дивиться вбік (rotated) |
| `yard-sign` | Табличка "Protected by..." на газоні |
| `floodlight` | Ліхтар + cone of light |
| `motion-sensor` | Маленький датчик біля дверей |
| `handcuffs` | Іконка для CAUGHT screen |
| `house-cta` | Будинок з камерою для фінального екрана |
| `moon` | Декоративний місяць |

**Стиль ассетів:** flat, мінімалістичний, 2–3 кольори на ассет. Без реалізму.

---

## 6. КОЛЬОРОВА ПАЛІТРА

| Роль | Колір | Hex |
|------|-------|-----|
| Нічне небо | Темно-синій | `#0A0A1E` |
| Небо (градієнт) | Темний індіго | `#1A1A3E` |
| Вулиця | Асфальт | `#1C1C1C` |
| Будинки | Темно-сірий | `#2D2D3D` |
| Дахи | Темніший сірий | `#1E1E2E` |
| Акцент DANGER | Червоний | `#EF4444` |
| Акцент SUCCESS | Зелений | `#22C55E` |
| Акцент WARNING | Жовтий | `#FACC15` |
| Текст | Білий | `#FFFFFF` |
| Sub-text | Світло-сірий | `#A1A1AA` |
| CTA кнопка | Яскраво-зелений | `#22C55E` |

---

## 7. ТИПОГРАФІКА

| Роль | Шрифт | Розмір | Вага |
|------|-------|--------|------|
| Головний текст | Space Grotesk | 72–96px | 700 |
| Body текст | Space Grotesk | 36–42px | 400 |
| Mono (час) | JetBrains Mono | 28px | 400 |
| CTA кнопка | Space Grotesk | 48px | 700 |
| Мікро-текст | Space Grotesk | 24px | 400 |

**Важливо:** шрифти завантажуються через `@import` в `<style>` — один разовий запит при старті, після чого кешовані. Meta дозволяє initial load запити.

---

## 8. META ТЕХНІЧНІ ВИМОГИ

- [x] Один `.html` файл
- [x] PixiJS + GSAP bundled inline (не CDN після старту)
- [x] Всі SVG ассети inline
- [x] `FbPlayableAd.onCTAClick()` на CTA кнопці
- [x] Canvas `1080×1920px`
- [x] Safe zone: верх/низ по 250px без інтерактивних елементів
- [x] Текст не більше 20% площі екрана
- [x] Мін. розмір шрифту: 28px
- [x] Файл < 2MB

---

## 9. ПЛАН РЕАЛІЗАЦІЇ

### Фаза 1 — Scaffolding (HTML + PixiJS init)
- [ ] HTML boilerplate з canvas 1080×1920
- [ ] PixiJS Application init
- [ ] GSAP підключення
- [ ] Screen manager (state machine: intro → street → outcome → stat → cta)

### Фаза 2 — Background Scene
- [ ] Нічне небо (градієнт через PixiJS Graphics)
- [ ] Місяць + зірки
- [ ] Вулиця (прямокутник)
- [ ] Вуличний ліхтар + світловий конус

### Фаза 3 — House Sprites
- [ ] Базовий будинок SVG → PixiJS Sprite
- [ ] House A: камера + знак + прожектор
- [ ] House B: без нічого
- [ ] House C: камера (rotated wrong angle)
- [ ] House D: вікно світиться + motion sensor
- [ ] Підписи A/B/C/D

### Фаза 4 — Thief Character
- [ ] SVG силует злодія
- [ ] Idle анімація (легке похитування)
- [ ] Run animation для outcome

### Фаза 5 — Interaction Logic
- [ ] Tap/click handler на кожному будинку
- [ ] Hover glow effect
- [ ] Idle pulse підказка після 4 сек

### Фаза 6 — Outcome Animations
- [ ] CAUGHT: red flash + handcuffs drop
- [ ] VULNERABLE: зелений → червоний fade
- [ ] STARTLED: жовтий flash + thief run

### Фаза 7 — Stat + CTA Screen
- [ ] Counter animation 0→83
- [ ] CTA screen build
- [ ] FbPlayableAd.onCTAClick() інтеграція
- [ ] Fallback: якщо API недоступне (preview mode)

### Фаза 8 — Polish + Optimization
- [ ] Перевірка розміру файлу
- [ ] Safe zone audit
- [ ] Тест в мобільному браузері (Chrome DevTools 390×844)
- [ ] Тест без звуку (Meta muted by default)
- [ ] Перевірка < 2MB

---

## 10. DELIVERABLE

```
verticals/home-security/playables/thief-pov/
├── TZ.md                  ← цей файл
├── thief-pov.html         ← фінальний файл для Meta
└── preview-notes.md       ← нотатки після тесту
```

Фінальний файл: `thief-pov.html`
Готовий до завантаження в: Meta Ads Manager → Playable Ads
