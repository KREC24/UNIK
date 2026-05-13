# UNIK ERP — Контекст проекта для AI-агентов

## Что это за проект
ERP-система UNIK для строительного холдинга, специализирующегося на **огнезащите (ОГЗ)** металлоконструкций.
Стек: **Python (FastAPI) + PostgreSQL + React**.

## Бизнес-процессы (6 этапов)

| № | Этап | Ответственный | ЦКП |
|---|------|--------------|-----|
| 1 | Обработка ПСД | РОП | Пакет чертежей КМ/КМД |
| 2 | Технический анализ ОГЗ | Гл. инженер | Ведомость площадей и приведённой толщины |
| 3 | Проработка себестоимости | Снабжение | Спецификация ОГЗ-составов с ценами |
| 4 | Планирование производства | Нач. участка | График нанесения ОГЗ |
| 5 | Формирование КП | Менеджер | КП с расчётом материалов |
| 6 | Договор | Юрист | Подписанный контракт |

**Ядро автоматизации: 1 → 2 → 5**

## Структура проекта

```
UNIK/
├── backend/
│   ├── app/
│   │   ├── main.py                     # FastAPI entry
│   │   ├── config.py                   # Settings (pydantic-settings)
│   │   ├── api/routes/
│   │   │   ├── parser.py               # POST /api/v1/parse/upload, GET preview/export
│   │   │   └── projects.py             # GET/POST /api/v1/projects
│   │   ├── core/
│   │   │   ├── parser_engine.py        # BaseParser (ABC)
│   │   │   ├── kmd_parser.py           # Парсер л.2 (Ведомость отправочных марок)
│   │   │   └── general_data_parser.py  # Парсер л.1 (Общие данные)
│   │   ├── models/database.py          # SQLAlchemy ORM (7 таблиц)
│   │   ├── schemas/parser.py           # Pydantic-схемы
│   │   └── services/
│   │       ├── parsing_service.py      # Оркестрация парсинга
│   │       └── export_service.py       # JSON/CSV/XLSX экспорт
│   ├── alembic/                        # Миграции БД
│   ├── scripts/test_parser.py          # Тестовый скрипт
│   └── requirements.txt
├── frontend/src/                       # React (будет заполняться)
├── docs/architecture.md                # Архитектурный план
├── testdoc/                            # Входные PDF (КМД листы 1-16 + revC04)
└── testxl/                             # Эталонный Excel
```

## Ключевые модели БД (app/models/database.py)

- **Project** — проект (external_code, name, stage)
- **Client** — заказчик
- **DocumentBatch** — пакет загруженных PDF (batch_type, source_file, status)
- **LineItem** — строка ведомости: mark, type_name, quantity, dims X×Y×Z, unit/total weight, unit/total area, ogz_notes, profile_type, steel_grade
- **SteelProfile** — справочник профилей (profile_name, gost_code, steel_grade, unit_weight_kg)
- **OgzComposition** — ОГЗ-состав (name, composition_type, consumption_rate, price_per_kg)
- **CommercialOffer** — КП (project_id, total_area, total_weight, costs)

## API эндпоинты (существующие)

| Метод | Путь | Описание |
|---|---|---|
| POST | `/api/v1/parse/upload` | Загрузка PDF, авто-парсинг |
| GET | `/api/v1/parse/batches/{id}` | Статус пакета |
| GET | `/api/v1/parse/batches/{id}/preview` | Первые 100 строк |
| GET | `/api/v1/parse/batches/{id}/export/json` | Экспорт JSON |
| GET | `/api/v1/parse/batches/{id}/export/csv` | Экспорт CSV |
| GET | `/api/v1/parse/batches/{id}/export/xlsx` | Экспорт Excel |
| GET | `/api/v1/projects` | Список проектов |
| POST | `/api/v1/projects` | Создать проект |

## Соглашения по коду

1. **Новые парсеры**: наследуются от `BaseParser` (app/core/parser_engine.py), реализуют `extract_text()`, `detect_tables()`, `parse_rows()`, `extract_metadata()`
2. **Новые эндпоинты**: в `app/api/routes/`, регистрируются в `app/main.py`
3. **Схемы**: Pydantic в `app/schemas/`, ответ API всегда через схемы
4. **Результат парсинга**: `ParseResultSchema` (items: list[LineItemSchema], metadata, errors)
5. **Не трогать существующий код без явного указания** — только добавлять новое
6. **Кодировка**: UTF-8, русский текст в коде и комментариях допустим
7. **Запуск тестов**: `python backend/scripts/test_parser.py` из корня проекта

## Входные данные (testdoc/)

- `л.1 (Общие данные).pdf` — метаданные + сводная таблица профилей стали
- `л.2 (Ведомость отправочных марок).pdf` — основная таблица (404 строки, 100% распознано)
- `revC04.pdf` (34 стр.) — полный пакет КМД с историей изменений (07-24, 34-24, 136-24, 49-25)
- `л.3-16` — схемы расположения элементов, разрезы, фасады (графика)

## Эталон (testxl/)

`Shiping_list_выбр_18.04.25 по 5.2 ведомость.xls` — 543 строки, масса 263 812 кг, площадь 5 623 м²
