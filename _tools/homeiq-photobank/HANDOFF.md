# HomeIQ — Handoff для наступного Claude

## Що це

HomeIQ — локальний CLI-інструмент для автоматичного збору фотографій з сайтів домашніх сервісів (security, bathroom, hvac, roofing, solar і т.д.). Повністю безкоштовний, без хмари, працює офлайн.

**Стек:** Python 3.13, httpx, BeautifulSoup, SQLAlchemy (SQLite), Pillow, Camoufox

---

## Поточний стан

### Що вже зроблено і працює

| Компонент | Файл | Статус |
|---|---|---|
| 3-tier HTTP fetcher | `homeiq/crawler/fetcher.py` | ✅ робочий |
| Витяг зображень з HTML | `homeiq/crawler/extractors.py` | ✅ робочий |
| BFS краулер | `homeiq/cli/crawl_site.py` | ✅ робочий |
| Завантаження + SHA256 dedup | `homeiq/crawler/downloader.py` | ✅ робочий |
| Визначення ніші сайту | `homeiq/crawler/site_analyzer.py` | ✅ робочий |
| Пошук схожих сайтів (DDG) | `homeiq/crawler/search_client.py` | ✅ робочий |
| Валідація підрядника | `homeiq/crawler/site_analyzer.py` | ✅ робочий |
| Повний discovery pipeline | `homeiq/cli/discover_sites.py` | ✅ робочий |
| SQLite БД | `homeiq/db.py` | ✅ робочий |
| Конфіг | `config.yaml` + `homeiq/config.py` | ✅ робочий |
| Тести | `tests/` | ✅ 27/27 passing |

### Зібрані дані
- Ніша: **security**, 7 сайтів, ~2300 фото
- Папка: `data/security/{domain}/{section}/`
- БД: `photos.db`

### Відомі обмеження
- 78% фото в папці `unknown/` — section detector працює тільки по URL/alt-тексту
- forbes.com потрапив в попередньому запуску (виправлено в новому — додано валідатор + exclude_domains)
- vectorsecurity.com — JS SPA, навіть tier3 не витягує зображення

---

## Наступний крок — AI Vision Classifier

### Задача
Написати `.\classify.bat` — скрипт що читає всі фото з папки `unknown/`, відправляє в Gemini через OpenRouter і розкладає по правильних папках.

### Нові категорії (замість поточних 5)
```
hero          ← широкий банер, фон сторінки (вже є)
before_after  ← до/після (вже є)
installation  ← технік за роботою, монтаж в процесі (НОВА)
product       ← обладнання крупним планом (НОВА)
lifestyle     ← люди + продукт/дім (НОВА)
exterior      ← зовні будинку (НОВА)
interior      ← всередині приміщення (НОВА)
text_overlay  ← є текст/watermark поверх фото — потребує обробки (НОВА)
reject        ← логотип, іконка, карта, UI-елемент — в смітник (НОВА)
```

### Технічні рішення (погоджені з юзером)
- **Модель:** `google/gemini-2.0-flash-exp:free` через OpenRouter (безкоштовна)
- **Fallback модель:** `google/gemini-2.5-flash` якщо rate limit
- **Паралелізм:** asyncio + semaphore 5 concurrent запитів (обережно для free tier)
- **Запуск:** окрема команда `.\classify.bat`, НЕ вбудовано в crawler
- **API:** OpenRouter (OpenAI-сумісний), ключ в `config.yaml` або env var `OPENROUTER_API_KEY`

### Файли які треба створити
```
homeiq/classifier/
├── __init__.py
├── vision_client.py      ← обгортка OpenRouter/OpenAI SDK для vision запитів
└── batch_classifier.py   ← читає фото з unknown/, паралельні запити, переміщує файли

homeiq/cli/classify_photos.py  ← CLI точка входу

classify.bat              ← ярлик
```

### Що додати в config.yaml
```yaml
classifier:
  openrouter_api_key: ""        # або env var OPENROUTER_API_KEY
  model: "google/gemini-2.0-flash-exp:free"
  fallback_model: "google/gemini-2.5-flash"
  max_concurrent: 5
```

### Промпт для моделі (концепт)
```
You are a photo classifier for a home services photo bank.
Look at this image and return ONLY one category name from this list:
- hero: wide banner or full-page background image
- before_after: split or paired before/after transformation photo
- installation: technician working, equipment being installed
- product: equipment or product close-up on clean background
- lifestyle: people interacting with product or home
- exterior: outside view of a house or building
- interior: inside view of a room
- text_overlay: photo with large text, watermark, or overlay that obscures the image
- reject: logo, icon, map, UI element, illustration, stock graphic

Return only the category name, nothing else.
```

### CLI інтерфейс
```
.\classify.bat [--niche security] [--folder unknown] [--dry-run] [--limit 100]
```

---

## Як запустити проект

### Встановлення
```bash
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
pip install camoufox playwright
playwright install chromium
python -m camoufox fetch
```

### Перевірка
```bash
python -m pytest tests/ -v   # має бути 27/27 passed
```

### Основні команди
```bash
# Знайти схожі сайти і зібрати фото
.\discover.bat https://www.vivint.com/ --sites 5 --max-pages 20

# Краулити конкретний сайт
.\crawl.bat https://www.bathfitter.com/ --niche bathroom

# Попередній перегляд без краулінгу
.\discover.bat https://www.sunrun.com/ --dry-run
```

---

## Структура проекту

```
homeiq/
├── config.yaml              ← всі налаштування
├── requirements.txt
├── crawl.bat                ← ярлик для crawl_site.py
├── discover.bat             ← ярлик для discover_sites.py
├── README.md                ← повна документація
├── homeiq/
│   ├── config.py
│   ├── db.py
│   ├── logger.py
│   └── crawler/
│       ├── fetcher.py       ← tier1(httpx) → tier2(jina) → tier3(camoufox)
│       ├── extractors.py
│       ├── link_extractor.py
│       ├── downloader.py
│       ├── section_detector.py
│       ├── site_analyzer.py
│       └── search_client.py
│   └── cli/
│       ├── crawl_site.py
│       └── discover_sites.py
└── tests/                   ← 27 тестів, всі passing
```

---

## Важливі технічні деталі

### SHA256 deduplication
Кожне фото хешується до завантаження. Дублікати скипаються без збереження на диск.

### Folder naming
`data/{niche}/{domain}/{section}/` — файли називаються `{sha256[:12]}.{ext}`

### DB schema
```python
class Photo(Base):
    sha256_hash, file_path, original_url, niche, section_tag,
    width, height, file_size, format, source, approved, detected_at, page_id

class Site(Base):
    domain, niche, seed_url, status

class Page(Base):
    site_id, url, last_scraped
```

### Конфіг (важливе)
`config.yaml` → `storage.base_dir` треба змінити на актуальний шлях після клонування.

### Windows-специфічне
- Консоль cp1251 — уникати Unicode символів в print() (─ → -)
- `removeprefix("www.")` НЕ `lstrip("www.")` — lstrip видаляє окремі символи!
- Camoufox subprocess через окремий worker щоб уникнути конфліктів asyncio на Windows

---

## Roadmap після classifier

1. **Видалення тексту** — inpainting для `text_overlay/` папки
2. **Більше ніш** — запустити discover для bathroom, solar, hvac, roofing...
3. **Веб UI** — перегляд і ручне схвалення фото
4. **API** — REST endpoint для зовнішнього доступу до фотобанку
