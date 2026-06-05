# Walk-In Shower Landings — Insights & Lessons

> Принципи для вертикалі walk-in-shower. **Читати перед будь-якою задачею на цих лендингах.**
> Формат тут — **quiz-прелендер**, а не повноцінний лендинг (як у home-security). Це інший жанр.

---

## 🎯 ЖАНР: QUIZ-ПРЕЛЕНДЕР (не плутати з повним лендингом)

- Завдання прелендера — НЕ продати, а **прогріти холодний платний трафік** і передати ліда у фанел.
- Конверсія = клік у `homeimprove.io/get-quotes/walk-in-shower/`, а не submit форми.
- Тому: мінімум тексту, бінарні YES/NO, нуль набору тексту, один повторюваний CTA.
- **Не перетворювати прелендер на повний лендинг** — це зламає його роль у воронці.

## 🚨 КРИТИЧНІ ПРАВИЛА

### 1. Quiz-питання = драбина мікрозобов'язань
- 3 тривіальних YES створюють інерцію перед головним кроком (consistency bias).
- Прогрес-бар додає goal-gradient (що ближче фініш — тим сильніше тягне завершити). Див. v2.
- **Не збільшувати кількість питань** — 3 це межа для холодного трафіку.

### 2. Офер треба заземлювати (copy-principle #1 + #2)
- Оригінал HomeQuotePro: "save thousands" без числа й причини = підозра.
- **Правильно:** число + причина + умова → "Up to $1,500 Off + Free Design Consult on any tub-to-shower conversion booked through the 2026 program". Див. v1.

### 3. Для візуальної покупки — потрібен візуальний доказ
- Ремонт ванної купують очима. Прелендер без фото втрачає довіру.
- **Before/after слайдер** — найсильніший елемент для цієї вертикалі. Див. v3.

### 4. Пом'якшувати агресивні елементи під наш tone of voice
- Прибрати "not part of Google/META", "act now" пресуре.
- Лишити чесний disclaimer: "free, no-obligation quote — bathrooms are not free".

### 5. "1-Day Install" — головний диференціатор вертикалі (з brief.md)
- Завжди виносити як бейдж/перк. Це те, чим walk-in-shower виграє в гонці уваги.

### 6. Окрема версія на кожен експеримент
- Кожна ідея = нова папка `vN-name/`. Не писати поверх baseline (це A/B контроль).
- Додати посилання в `INDEX.html`.

---

## 📐 ДИЗАЙН ТОКЕНИ (успадковані від джерела, спільні для всіх 4 версій)

```css
:root {
  --brand:#2563eb; --brand-dark:#1745aa;   /* CTA / links */
  --yes:#04ae15;  --no:#eb060a;             /* quiz buttons */
  --ink:#111827;  --body:#374151;           /* headings / text */
  --star:#f5a623;                            /* review stars */
  --page-bg:#f7f7f7; --card-bg:#fff; --radius:8px;
}
/* Font: Rubik (Google Fonts) */
```

---

## ✍️ TONE OF VOICE (з brief + copy-principles)

**Audience:** US homeowners 40–70, aging-in-place + remodelers. Practical, value-conscious.
**Use:** specific numbers (4.9★, $1,500 off, 1-day install), name+city social proof, accessibility benefits.
**Avoid:** vague "save thousands", "act now", spam-flavored disclaimers.
**CTA фрази:** "Check If I Qualify", "Get My Free Quote", "See If I Qualify →".

---

## 🔁 ПРОЦЕС ІТЕРАЦІЇ
1. Прочитати цей файл + `../brief.md` + `_playbook/copy-principles.md`.
2. Зрозуміти, який **один важіль** крутимо (офер / інтерактив / візуал / копі).
3. Нова папка `vN-name/`, self-contained, не поверх baseline.
4. Перевірити в preview (DOM/eval надійніше за screenshot, якщо рендер залипає).
5. Оновити `INDEX.html` + `CHANGELOG.md`. Новий принцип → сюди.

---

## 📚 РЕФЕРЕНСИ
- **HomeQuotePro** (`../references/home-quote-pro.md`) — джерело baseline, gold standard формату прелендера.
- Майбутні: Bath Fitter, Re-Bath, West Shore Home (full landings, для бенефітів/візуалу).
