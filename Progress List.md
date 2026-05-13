# Progress List — Журнал реализованного функционала UNIK ERP

> Начало разработки: 13.05.2026
> Назначение: единый реестр реализованных возможностей системы. Пополняется при каждом коммите.
> Язык: русский.

---

## 1. Архитектурный план

- Разработан масштабируемый скелет системы (Backend FastAPI + Frontend React + PostgreSQL)
- Задокументированы 6 этапов бизнес-процессов (Обработка ПСД → Тех.анализ ОГЗ → Себестоимость → Планирование → КП → Договор)
- Определены Ценные Конечные Продукты (ЦКП) для каждого этапа
- Спроектирована модульная структура: CRM (БП 1.1), Проектирование (БП 1.2), Снабжение (БП 1.3)
- Ядро автоматизации: этапы 1 → 2 → 5 (ПСД → Тех.анализ → КП)
- Файл: `docs/architecture.md`

## 2. База данных

- Спроектирована схема PostgreSQL: 7 таблиц (SQLAlchemy ORM)
- Таблицы: `projects`, `clients`, `document_batches`, `line_items`, `steel_profiles`, `ogz_compositions`, `commercial_offers`
- Миграции Alembic: 001_initial (все 7 таблиц), 002 (расширение полей приведённой толщины и составов)
- Типы: UUID первичные ключи, Decimal для точных расчётов, JSON для гибких контактов
- Индексы: по external_code (проекты), mark (строки ведомости), profile_name (справочник профилей)
- Файл: `backend/app/models/database.py`

## 3. Парсер PDF (Parser Engine)

### 3.1 Базовый движок
- Абстрактный класс `BaseParser` с конвейером: `extract_text()` → `detect_tables()` → `parse_rows()` → `validate_row()` → `parse()`
- Валидация: проверка обязательных полей (mark, quantity), корректность чисел (масса ≥ 0)
- Логирование нераспознанных строк с указанием причины
- Файл: `backend/app/core/parser_engine.py`

### 3.2 Парсер ведомости отправочных марок (л.2 КМД)
- State-machine разбор 11-полных чанков: Поз → Марка → Наименование → Кол-во → Габариты (X×Y×Z) → Масса (ед./общ.) → Площадь (ед./общ.)
- Поддержка дублированных 6-колоночных блоков (66 полей в строке → 6 элементов × 11 полей)
- Результат: **404/404 строки (100%), масса 236 545 кг, площадь 4 921 м²**
- Файл: `backend/app/core/kmd_parser.py`

### 3.3 Парсер общих данных (л.1 КМД)
- Извлечение метаданных: шифр проекта, объект, стадия
- Сводная таблица металлопрофилей: 116 позиций (I25Ш1, L75x5, [20П, Гн.40×3...)
- Классификация профилей: двутавр (beam), швеллер (channel), уголок (angle), труба (pipe), гнутый (bent_section)
- Автоопределение типа документа по имени файла
- Файл: `backend/app/core/general_data_parser.py`

### 3.4 Парсер revC04 (основной пакет КМД, 34 стр.)
- Извлечение 45 строк с марками из 34-страничного PDF
- Авторемонт кодировки (cp1251 в Latin-1 интерпретации)
- Извлечение профилей стали: двутавр (16), труба (26), швеллер (2), уголок (1)
- Марки стали: С345-5 (22), С255-5 (23)
- Файл: `backend/app/core/revC04_parser.py`

## 4. Модуль расчёта ОГЗ (OGZ Calculator)

- Расчёт приведённой толщины металла: δ_пр = M / (S × 7850) мм
- Подбор ОГЗ-состава по пределу огнестойкости (REI 30/60/90/120/150) и среде (сухая/влажная/агрессивная)
- Расчёт расхода материалов: грунт = S × N_grunt, краска = S × δ × N_kraska, финиш = S × N_finish
- API: `POST /api/v1/ogz/calculate`, `GET /api/v1/ogz/compositions`, `POST /api/v1/ogz/compositions`
- Справочник ОГЗ-составов: ГФ-021 (грунт), Термобарьер (краска), ПФ-115 (финиш) — 6 позиций
- Файлы: `backend/app/core/ogz_calculator.py`, `backend/app/services/ogz_service.py`, `backend/app/schemas/ogz.py`, `backend/app/api/routes/ogz.py`

## 5. API эндпоинты

| Метод | Путь | Назначение |
|-------|------|------------|
| POST | `/api/v1/parse/upload` | Загрузка PDF, авто-парсинг (типы: shipping, general, revC04, auto) |
| GET | `/api/v1/parse/batches/{id}` | Статус пакета |
| GET | `/api/v1/parse/batches/{id}/preview` | Предпросмотр (первые 100 строк) |
| GET | `/api/v1/parse/batches/{id}/export/json` | Экспорт JSON |
| GET | `/api/v1/parse/batches/{id}/export/csv` | Экспорт CSV |
| GET | `/api/v1/parse/batches/{id}/export/xlsx` | Экспорт Excel |
| GET | `/api/v1/projects` | Список проектов |
| POST | `/api/v1/projects` | Создать проект |
| GET | `/api/v1/projects/{id}` | Детали проекта (включая batches) |
| POST | `/api/v1/ogz/calculate` | Расчёт ОГЗ-спецификации |
| GET | `/api/v1/ogz/compositions` | Справочник составов |
| POST | `/api/v1/ogz/compositions` | Добавить состав |
| GET | `/api/v1/clients` | Список клиентов |
| POST | `/api/v1/clients` | Создать клиента |
| GET | `/api/v1/clients/{id}` | Детали клиента |

**Всего: 15 эндпоинтов**

## 6. Фронтенд (React SPA)

- Стек: Vite + React 19 + TypeScript + Ant Design 5 + React Router 7
- Сборка: 0 ошибок TypeScript, production bundle OK
- Маршруты: `/` (Проекты), `/upload` (Загрузка PDF), `/projects/:id` (Детали проекта), `/clients` (Клиенты)

### 6.1 Страницы
- **Dashboard** — таблица проектов с навигацией, кнопки «Загрузить PDF» и «Новый проект»
- **ProjectDetail** — drag-and-drop загрузка PDF → парсинг → таблица результатов (9 колонок) + кнопки экспорта JSON/CSV/Excel
- **ClientsPage** — CRUD клиентов (таблица + модальная форма создания)

### 6.2 Компоненты
- **PdfUploader** — загрузка PDF с прогресс-баром, drag-and-drop, сообщение о результате
- **LineItemsTable** — таблица строк ведомости: Поз, Марка, Наименование, Кол-во, Габариты, Масса (ед./общ.), Площадь (ед./общ.), итоги по массе и площади
- **App** — боковое меню (сворачиваемое) + область контента, тёмная/светлая тема

### 6.3 Интеграция с API
- Axios-инстанс с baseURL `http://localhost:8000/api/v1`
- Типизированные функции: `uploadPdf()`, `getBatchPreview()`, `getExportUrl()`, `getProjects()`, `getClients()`
- TypeScript-интерфейсы: Project, LineItem, ParseResult, BatchPreview, Client, Metadata

## 7. Инфраструктура проекта

- **Агенты**: 3 AI-агента (Parser, OGZ, CRM) с полным контекстом в `.kilo/agent/`
- **Контекст**: `AGENTS.md` — единый файл контекста для всех моделей
- **Конфигурация**: `kilo.json` — стек, пути, линтинг, агенты
- **Тестирование**: `backend/scripts/test_parser.py` — запуск парсеров на testdoc
- **Сид-данные**: `backend/scripts/seed_ogz.py` — 6 составов с полными параметрами (PTM-диапазоны, dry_residue, density, REI, среда)

## 8. Исправления (Bugfixes)

### 8.1 Тест OGZ-калькулятора (CRITICAL)
- `backend/scripts/test_ogz.py` импортировал удалённые функции `select_ogz_composition` и `calculate_material_consumption`
- Переписан на новый API: `match_compositions()`, `calculate_ogz_full()`
- Добавлены тестовые составы с полными параметрами (PTM-диапазоны, dry_residue, density)
- Все 4 теста проходят

### 8.2 Сид-данные ОГЗ-составов (WARNING)
- `backend/scripts/seed_ogz.py`: SEED_DATA дополнен полями `dry_residue`, `density`, `min_ptm_mm`, `max_ptm_mm`, `rei_minutes`, `environment`
- Без них PTM-матчинг не фильтровал составы по толщине

---

*Последнее обновление: 13.05.2026 — исправлены баги OGZ-модуля*
