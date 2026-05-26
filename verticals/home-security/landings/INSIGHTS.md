# Home Security Landings — Design Insights & Lessons Learned

> Постійний список принципів і правил, які виведені з фідбеку PM.
> **Перед будь-якою новою задачею на лендінгах — прочитати цей файл.**

---

## 🚨 КРИТИЧНІ ПРАВИЛА (порушувати не можна)

### 1. HERO — це фото + один сильний меседж, а не текстова стіна
- Юзер бачить hero за **1 секунду** і вирішує залишатись.
- Якщо немає візуального якоря (фото) — губимо ліда.
- Якщо забагато тексту і опцій — paralysis, юзер тікає.
- **Дотримуватись правила: 1 фото + 1 заголовок + 1 СTA.**

### 2. Форма НЕ перекриває hero photo
- Колись зробив форму як `position: absolute` поверх фото — це самосаботаж.
- Юзер не бачить продукт → не розуміє що йому пропонують.
- **Або форма поряд (side-by-side), або в окремій секції під hero.**

### 3. CTA в hero має бути кінцевим, а не проміжним
- "Check Availability ↓" що скролить до форми = зайвий рух для юзера.
- **Або кнопка веде на справжню конверсію (телефон tel: / форма), або її прибираємо.**
- Найкраще — **клікабельна телефонна pill** (як Vivint).

### 4. На мобайлі — фото EDGE-TO-EDGE, без shadow/border-radius
- Коли photo має shadow і closed border-radius на тлі темного hero — мозок читає це як "окремий card".
- **Зробити фото повноекранним без decoration → photo стає природньою частиною hero.**

### 5. Hero має поміщатися в 1 екран (особливо на мобайлі)
- Інакше юзер втомлюється скролити і не доходить до офера.
- **`min-height: calc(100vh - 70px)`** на hero + контроль розміру тексту/перків.

### 6. Завжди робити ОКРЕМУ ВЕРСІЮ для експериментів
- НЕ писати поверх робочого. Раз вже втрачали teal версію — більше не можна.
- **Кожна нова ідея = нова папка `vN-name/`.**
- Якщо проект складний — додати в `INDEX.html` посилання.

### 7. Trust bar має бути впорядкованим, не випадковим
- 5 елементів у 2 колонки = висить, виглядає крива.
- **Зробити кратним: 4 (2×2), 6 (3×2), 8 (4×2).**
- Усі іконки **одного візуального стилю** (всі pill, всі lined, тощо).

### 8. Текст на heró — UPPERCASE BOLD як на Vivint
- Маленький eyebrow ("MEMORIAL DAY SALE") +
- Великий заголовок ("UP TO **6 MONTHS FREE MONITORING**\*") +
- Subtitle одним рядком.
- Чи `GET 6 MONTHS FREE MONITORING` залежно від офера.

---

## 🎯 АРХІТЕКТУРНІ РІШЕННЯ

### Структура папок
```
landings/
├── INSIGHTS.md          ← цей файл
├── INDEX.html           ← навігація між версіями
├── CHANGELOG.md         ← історія змін
├── _shared/             ← privacy, terms, contact
│   ├── privacy-policy.html
│   ├── terms-of-use.html
│   └── contact.html
├── v1-upgrade-security/ ← оригінальний live ленд (синій)
├── v1-install-direct/   ← оригінальний live ленд (vivint promo)
├── v2-improved/         ← brand-neutral вдосконалена версія
├── v3-vivint-inspired/  ← v1 base + vivint CSS override
├── v4-product-led/      ← teal/чорний Vivint-style, doorbell hero
├── v4b-hero-lineup/     ← v4 + product lineup hero
├── v4c-hero-camera/     ← v4 + outdoor camera hero
├── v4d-hero-fullbleed/  ← image як full bg + inline trust strip
├── v4e-hero-split/      ← hard 50/50 split + award logos trust
├── v4f-hero-card/       ← dark card hero + metric grid trust
├── v5-blue-product-led/ ← blue палітра, doorbell hero
├── v5b-blue-lineup/     ← blue + lineup hero
└── v5c-blue-camera/     ← blue + outdoor camera hero
```

### Naming convention
- `v{N}-{descriptor}/` — головна версія
- `v{N}{letter}-{descriptor}/` — варіант тієї ж версії (різна фото/trust bar)
- Файли всередині завжди self-contained (inline CSS+JS) щоб не залежати від CDN/shared assets

### Технічний stack
- HTML5, CSS3 (inline в `<style>`), vanilla JS
- Google Fonts (Inter)
- Без фреймворків, без бандлерів
- Все фото локально в `images/` папці кожного ленда

---

## 📐 ДИЗАЙН ТОКЕНИ (приклад v4 teal)

```css
:root {
  --brand:     #05E5AF;   /* Vivint teal */
  --black:     #000000;
  --gray-100:  #f5f5f5;
  --gray-200:  #e5e5e5;
  --gray-500:  #737373;
  --shadow-md: 0 4px 16px rgba(0,0,0,0.12);
  --radius:    12px;
  --radius-lg: 20px;
}
```

## 📐 ДИЗАЙН ТОКЕНИ (v5 blue Vivint)

```css
:root {
  --brand:        #004F9F;   /* Vivint blue */
  --brand-hover:  #003D7F;
  --brand-light:  #4A90D9;
  --hero-grad-1:  #B6D4F0;
  --hero-grad-2:  #6DAEE4;
}
```

---

## ✍️ TONE OF VOICE

**Audience:** US homeowners, age 35–65, practical, value-conscious
**Tone:** Trustworthy, knowledgeable, no-pressure
**Avoid:** jargon, aggressive sales language, empty superlatives
**Use:** specific numbers (4.8★, 2,400+ reviews), social proof, local relevance signals

### Дозволені CTA фрази
- "Check Availability" — нейтральний
- "Get Free Quote" — directly value
- "Claim Offer" — promo-driven
- "Call Now" — phone-focused

### Заборонено
- "Sign up", "Subscribe" — не в стилі lead-gen
- "Limited time only!!!" — too aggressive
- Будь-яке "act now" пресуре

---

## 🔁 ПРОЦЕС ІТЕРАЦІЇ

1. Прочитати INSIGHTS.md
2. Зрозуміти що користувач хоче (запитати якщо неясно)
3. Створити **окрему версію**, не писати поверх робочого
4. Зробити mobile + desktop screenshots
5. Перевірити: фото видно? CTA не перекриває? text не задовгий? spacing розумний?
6. Оновити `INDEX.html` посиланням на нову версію
7. Якщо отримали новий принцип/правило → додати в INSIGHTS.md

---

## 📅 ХРОНОЛОГІЯ ЗМІН (high-level)

| Дата | Що зроблено |
|------|------------|
| Травень 2026 | Extract v1 з live сайтів, fixed Swiper height / Slick lazyload |
| Травень 2026 | v3-vivint — спроба з нуля, відхилено: спочатку треба було взяти оригінал v1 і застосувати vivint CSS override |
| Травень 2026 | v3-vivint v2 — правильно: v1 base + vivint CSS, отримали teal/чорний look |
| Травень 2026 | v4-product-led — повний редизайн з продуктовою структурою (Vivint mobile вертикальний референс) |
| Травень 2026 | Помилка: спочатку зробив hero з overlay form, потім переробив без overlay |
| Травень 2026 | v4 → v4b/v4c (різні фото), v5/v5b/v5c (синя палітра) |
| Травень 2026 | v4d/v4e/v4f — 3 переосмислені hero (fullbleed, split, card) з різними trust bar variants |
| Травень 2026 | Phone pill CTA (як Vivint) замість "Check Availability ↓" |

---

## 📚 РЕФЕРЕНСИ

- **Vivint home page** (vivint.com/home-security) — gold standard для hero
- **SimpliSafe** — product lineup на dark blue + orange bg (сам lineup photo взято звідти)
- **ADT** — credibility через award logos (Newsweek, PCMag)
- **Frontpoint** — DIY + monitoring positioning
- **Cove** — мінімалізм у trust signals
