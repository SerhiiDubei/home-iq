# HomeIQ Photo Bank

Локальний інструмент для автоматичного збору та класифікації фотографій з сайтів домашніх сервісів.
Скрапить фото, AI-сортує по категоріях, зберігає в SQLite.

**Повністю локальний. Не потребує хмарного сховища. $0 інфраструктура.**

---

## Зміст

- [Архітектура](#архітектура)
- [Встановлення](#встановлення)
- [Швидкий старт](#швидкий-старт)
- [Команди](#команди)
- [Структура папок](#структура-папок)
- [Конфігурація](#конфігурація)
- [Пайплайн](#пайплайн)
- [Результати](#результати)
- [Наступні етапи](#наступні-етапи)

---

## Архітектура

```
homeiq/
├── config.py                ← завантаження config.yaml
├── db.py                    ← SQLite БД (Sites, Pages, Photos)
├── logger.py                ← налаштування логування
├── crawler/
│   ├── fetcher.py           ← 3-tier HTTP fetcher
│   ├── extractors.py        ← витяг img/srcset/og:image з HTML
│   ├── link_extractor.py    ← витяг внутрішніх посилань (BFS)
│   ├── downloader.py        ← завантаження + SHA256 dedup + валідація
│   ├── section_detector.py  ← базове визначення секції по URL
│   ├── site_analyzer.py     ← визначення ніші + валідація підрядника
│   └── search_client.py     ← пошук схожих сайтів через DuckDuckGo
├── classifier/
│   ├── vision_client.py     ← AI класифікатор (Gemini via OpenRouter)
│   └── batch_classifier.py  ← batch обробка + prefilter + review queue
└── cli/
    ├── crawl_site.py        ← краулінг одного сайту
    ├── discover_sites.py    ← повний пайплайн: аналіз → пошук → краулінг
    └── classify_photos.py   ← AI класифікація фото
```

### 3-Tier Fetcher

| Tier | Метод | Швидкість | Коли |
|------|-------|-----------|------|
| **1** | `httpx` напряму | ~1 сек | Більшість сайтів |
| **2** | `r.jina.ai` proxy | ~4 сек | Сайти з 403 блокуванням |
| **3** | `Camoufox` headless | ~8-30 сек | SPA / JS-rendered |

### AI Класифікатор

**Модель:** `google/gemini-2.5-flash` via OpenRouter

**Категорії:**

| Категорія | Що туди йде |
|---|---|
| `hero` | Широкий маркетинговий банер |
| `before_after` | До/після — два стани одного предмету |
| `installation` | Технік за роботою, видно інструменти |
| `product` | Обладнання на чистому фоні |
| `lifestyle` | Люди природно взаємодіють з продуктом |
| `exterior` | Зовні будівлі |
| `interior` | Всередині приміщення |
| `text_overlay` | Фото з великим текстом/watermark |
| `portrait` | Портрет/headshot співробітника |
| `reject` | Логотип, іконка, UI скрін, ілюстрація |
| `review/` | Низька впевненість — потребує перегляду |

**Pre-filters (без API):**
- Зображення < 250px → reject
- Solid-color (std < 18) → reject
- Портретна орієнтація + hero/lifestyle → portrait

**Confidence routing:**
- ≥ 82% → автофайл
- 55-82% → файл + мітка `needs_review`
- < 55% → папка `review/` для ручного перегляду

---

## Встановлення

```bash
# 1. Клонувати
git clone <repo> homeiq
cd homeiq

# 2. Створити venv
python -m venv venv
.\venv\Scripts\activate       # Windows
# source venv/bin/activate    # Linux/Mac

# 3. Встановити залежності
pip install -r requirements.txt
pip install camoufox playwright
playwright install chromium
python -m camoufox fetch

# 4. Перевірити
python -m pytest tests/ -v     # має бути 42/42 passed
```

---

## Швидкий старт

### 1. Знайти схожі сайти і скрапити

```bash
.\discover.bat https://www.vivint.com/ --sites 5 --max-pages 20
```

### 2. Класифікувати фото через AI

Потрібен OpenRouter API ключ → [openrouter.ai](https://openrouter.ai) (безкоштовна реєстрація)

```bash
# Додати ключ в config.yaml:
# classifier.openrouter_api_key: "sk-or-..."

# Dry-run (без переміщення файлів)
.\classify.bat --niche security --dry-run

# Реальна класифікація
.\classify.bat --niche security
```

---

## Команди

### `discover.bat` — головна команда

```
.\discover.bat <url> [опції]

  url               Референсний сайт (обов'язково)
  --sites N         Скільки схожих сайтів знайти (default: 5)
  --max-pages N     Сторінок на сайт (default: 20)
  --dry-run         Тільки показати знайдені сайти, не краулити

Приклади:
  .\discover.bat https://www.vivint.com/
  .\discover.bat https://www.bathfitter.com/ --sites 8 --max-pages 30
  .\discover.bat https://www.sunrun.com/ --dry-run
```

### `crawl.bat` — краулінг одного сайту

```
.\crawl.bat <url> [опції]

  url               Стартова URL (обов'язково)
  --niche NAME      Ніша (auto-detect якщо не вказано)
  --max-pages N     Ліміт сторінок (default: 100)

Приклади:
  .\crawl.bat https://www.vivint.com/ --niche security
  .\crawl.bat https://www.bathfitter.com/
```

### `classify.bat` — AI класифікація

```
.\classify.bat [опції]

  --niche NAME      Тільки ця ніша (default: всі)
  --folder PATH     Конкретна папка замість unknown/
  --dry-run         Показати результат без переміщення
  --limit N         Тільки перші N фото
  --model NAME      Перевизначити модель

Приклади:
  .\classify.bat
  .\classify.bat --niche security --dry-run
  .\classify.bat --folder data\security\vivint.com\unknown
  .\classify.bat --niche bathroom --limit 100
```

---

## Структура папок

```
data/
└── {ніша}/
    └── {домен}/
        ├── hero/
        ├── product/
        ├── lifestyle/
        ├── installation/
        ├── exterior/
        ├── interior/
        ├── before_after/
        ├── text_overlay/
        ├── portrait/
        ├── reject/
        ├── review/          ← низька впевненість AI
        └── unknown/         ← ще не класифіковано

photos.db                    ← SQLite база даних
```

**Підтримувані ніші:** bathroom, flooring, hvac, security, shower, siding, gutter, home_warranty, kitchen, plumbing, roof, solar, walk_in_tubs

---

## Конфігурація

`config.yaml`:

```yaml
storage:
  base_dir: "D:/CloudeCode/homeiq"   # ← змінити на свій шлях

crawler:
  request_delay: 1.5        # затримка між сторінками (сек)
  max_pages: 100
  min_dimension_px: 100     # мінімум для завантаження
  min_file_bytes: 500

classifier:
  openrouter_api_key: ""    # або env var OPENROUTER_API_KEY
  model: "google/gemini-2.5-flash"
  fallback_model: "google/gemini-2.5-flash"
  max_concurrent: 5         # паралельних запитів
  cost_per_image_usd: 0.0001

discovery:
  max_sites: 10
  skip_crawled_domains: true

exclude_domains:            # ці домени не краулити
  - pinterest.com
  - forbes.com
  - cnet.com
  # ... та інші
```

---

## Пайплайн

```
.\discover.bat <url>
       ↓
[site_analyzer] Визначення ніші по title/meta/h1
       ↓
[search_client] DuckDuckGo → знаходить 10-20 кандидатів
       ↓
[is_contractor_site()] Відсіює новинні/review сайти
       ↓
BFS crawler для кожного сайту:
  [fetcher tier1/2/3] → [extractors] → [downloader + SHA256 dedup]
       ↓
data/{niche}/{domain}/unknown/

.\classify.bat
       ↓
[prefilter] < 250px або solid-color → reject (без API)
       ↓
[Gemini 2.5 Flash] → JSON {"category", "confidence", "runner_up", "reason"}
       ↓
[postfilter] Геометричні перевірки (AR, orientation)
       ↓
confidence ≥ 82% → category/
confidence < 55% → review/
інакше          → category/ + needs_review tag
```

---

## Результати

### Поточний датасет (security ніша)

| Категорія | Фото |
|---|---|
| product | 654 |
| reject | 596 |
| hero | 339 |
| lifestyle | 288 |
| interior | 103 |
| text_overlay | 89 |
| exterior | 88 |
| installation | 75 |
| before_after | 14 |
| **Всього** | **~2,261** |

**7 сайтів:** vivint.com, ajax.systems, guardianprotection.com, safestreets.com, safehomesecurityinc.com, skylinesecurity.com, adt.com

### Benchmark класифікатора

| Категорія | Точність |
|---|---|
| exterior | ~100% |
| product | ~90% |
| interior | ~85% |
| lifestyle | ~80% |
| hero | ~75% |
| before_after | ~70% |
| installation | ~60% |

**Ціна:** ~$0.0001/фото → 2000 фото ≈ **$0.20**
**Швидкість:** ~3 фото/сек (5 паралельних запитів)

---

## Наступні Етапи

### Етап 2 — Більше ніш
```bash
.\discover.bat https://www.bathfitter.com/    # bathroom
.\discover.bat https://www.sunrun.com/        # solar
.\discover.bat https://www.lennox.com/        # hvac
```

### Етап 3 — Видалення тексту
Inpainting для фото в `text_overlay/` папці.

### Етап 4 — Review UI
Простий локальний UI для перегляду `review/` папки з one-click схваленням.

### Етап 5 — Golden set + eval harness
300-500 вручну лейблованих фото → confusion matrix → об'єктивна метрика якості.

### Етап 6 — API
REST endpoint для доступу до фотобанку з зовнішніх інструментів.

---

*Останнє оновлення: червень 2026*
