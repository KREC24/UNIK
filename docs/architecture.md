# UNIK ERP — Архитектура системы

## 1. Обзор

UNIK — единая ERP-экосистема строительного холдинга для автоматизации:
- Первичной обработки проектной документации (КМ/КМД)
- Технического анализа ОГЗ (огнезащита): расчёт площадей и приведённой толщины
- Проработки себестоимости и снабжения
- Формирования коммерческих предложений (КП)

Стек: **Python (FastAPI) + PostgreSQL + React**

---

## 2. Карта бизнес-процессов и ЦКП

| № | Этап процесса | Ответственный | Ценный Конечный Продукт (ЦКП) |
|---|---|---|---|
| 1 | Обработка запроса и ПСД | РОП | Полный пакет чертежей КМ/КМД, готовый к анализу |
| 2 | Технический анализ (ОГЗ) | Главный инженер | Ведомость с расчётом площадей поверхности и приведённой толщины металла |
| 3 | Проработка себестоимости | Снабжение | Спецификация ОГЗ-составов, грунтов и финишных покрытий с ценами |
| 4 | Планирование производства | Нач. участка | График нанесения ОГЗ, расчёт человеко-часов и оборудования |
| 5 | Формирование КП | Менеджер продаж | КП с точным расчётом расхода материалов и стоимости работ |
| 6 | Договор | Юрист | Подписанный контракт, запуск СМР |

**Ядро автоматизации: этапы 1 → 2 → 5** (обработка ПСД → тех.анализ → КП)

---

## 3. Модульная структура

```
┌──────────────────────────────────────────────────────┐
│                    FRONTEND (React)                   │
│  ┌─────────┐ ┌──────────┐ ┌────────┐ ┌───────────┐  │
│  │  CRM    │ │ Проекты  │ │ Склад  │ │  Отчёты   │  │
│  │ (БП1.1) │ │ (БП1.2)  │ │(БП1.3) │ │           │  │
│  └─────────┘ └──────────┘ └────────┘ └───────────┘  │
├──────────────────────────────────────────────────────┤
│                  BACKEND (FastAPI)                    │
│  ┌─────────────────────────────────────────────────┐ │
│  │              API Gateway / Router                │ │
│  ├──────────┬──────────┬───────────┬──────────────┤ │
│  │  Parser  │  CRM     │  Design   │  Supply      │ │
│  │  Module  │  Module  │  Module   │  Module      │ │
│  │  (ядро)  │ (БП 1.1) │ (БП 1.2)  │ (БП 1.3)    │ │
│  ├──────────┴──────────┴───────────┴──────────────┤ │
│  │            Parser Engine (extensible)           │ │
│  │  ┌────────────┐ ┌────────────┐ ┌────────────┐  │ │
│  │  │ KMD Parser │ │ VOR Parser │ │ SpecParser │  │ │
│  │  └────────────┘ └────────────┘ └────────────┘  │ │
│  ├─────────────────────────────────────────────────┤ │
│  │          Services / Business Logic              │ │
│  ├─────────────────────────────────────────────────┤ │
│  │          PostgreSQL (SQLAlchemy + asyncpg)      │ │
│  └─────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────┘
```

---

## 4. Схема базы данных

### 4.1 Основные сущности

```
projects
├── id (UUID PK)
├── external_code (str)       — шифр проекта (В068522/1540Д-416-55500-01-5.2-КМД)
├── name (str)                — название объекта
├── stage (str)               — стадия (П, Р, КМД)
├── client_id (FK → clients)
├── created_at, updated_at

clients
├── id (UUID PK)
├── name (str)
├── inn (str)
├── contacts (jsonb)

document_batches               — пакет загруженных PDF
├── id (UUID PK)
├── project_id (FK → projects)
├── batch_type (enum)         — KMD, VOR, SPEC, GENERAL
├── source_file (str)         — имя исходного PDF
├── page_count (int)
├── status (enum)             — uploaded, parsing, parsed, verified, error
├── parsed_at
├── created_at

line_items                     — строки ведомости (ЦКП этапа 1→2)
├── id (UUID PK)
├── batch_id (FK → document_batches)
├── project_id (FK → projects)
├── source_sheet (str)        — л.2, л.1, etc.
├── position (int)            — номер позиции
├── mark (str)                — марка (A-1, BK1-3, ...)
├── type_name (str)           — наименование (рама, балка, колонна...)
├── quantity (decimal)
├── length_x (decimal, mm)
├── width_y (decimal, mm)
├── height_z (decimal, mm)
├── unit_weight_kg (decimal)
├── total_weight_kg (decimal)
├── unit_area_m2 (decimal)
├── total_area_m2 (decimal)
├── ogz_notes (str)           — пометки ОГЗ
├── profile_type (str)        — тип профиля (из КМД: двутавр, швеллер...)
├── steel_grade (str)         — марка стали (С345-5, С255-5)
├── gost_code (str)           — ГОСТ профиля
├── status (enum)             — raw, verified, rejected
├── parse_confidence (float)  — уверенность парсинга 0..1
├── raw_text (text)           — исходная строка для аудита
├── created_at

steel_profiles                 — справочник металлопрофилей (из л.1)
├── id (UUID PK)
├── profile_name (str)        — I25Ш1, L75x5, [20П...
├── gost_code (str)
├── steel_grade (str)
├── unit_weight_kg (decimal)
├── section_type (str)        — beam, channel, angle, pipe, plate...

ogz_compositions               — справочник ОГЗ-составов
├── id (UUID PK)
├── name (str)                — название состава
├── type (enum)               — грунт, краска, финиш
├── consumption_rate (decimal)— расход кг/м²/мм толщины
├── price_per_kg (decimal)
├── supplier_id (FK → suppliers)

commercial_offers              — КП (ЦКП этапа 5)
├── id (UUID PK)
├── project_id (FK → projects)
├── calculated_at
├── total_area_m2 (decimal)
├── total_weight_kg (decimal)
├── material_cost (decimal)
├── work_cost (decimal)
├── total_cost (decimal)
├── status (enum)             — draft, sent, signed
```

---

## 5. Архитектура парсера (Parser Engine)

Принципы:
1. **Модульность** — базовый класс `BaseParser` с абстрактными методами `extract_tables()`, `normalize_fields()`, `validate_row()`.
2. **Семантический поиск** — поиск ключевых слов в тексте, а не привязка к координатам.
3. **Конвейер обработки**: PDF → Text Extraction → Table Detection → Column Mapping → Row Extraction → Validation → JSON/DB.

```python
class BaseParser(ABC):
    """Абстрактный парсер строительной документации."""
    @abstractmethod
    def extract_tables(self, text: str) -> list[list[str]]:
        """Извлечь таблицы из текстового потока."""
        ...

    @abstractmethod
    def map_columns(self, headers: list[str]) -> dict[str, int]:
        """Сопоставить заголовки с полями модели."""
        ...

    @abstractmethod
    def parse_row(self, row: list[str], mapping: dict) -> dict | None:
        """Разобрать строку в словарь полей."""
        ...

    def validate_row(self, item: dict) -> tuple[bool, list[str]]:
        """Валидация: наличие обязательных полей, корректность чисел."""
        ...
```

### 5.1 KmdShippingParser (л.2 — Ведомость отправочных марок)

- Ищет заголовки: «Марка», «Кол-во», «Масса», «Площадь», «Габарит»
- Обнаруживает дублированные 6-колоночные блоки
- Разбивает строку на чанки по 11 полей (Поз + Марка + Описание + Кол-во + X×Y×Z + Масса ед/общ + S ед/общ)
- Применяет regex для идентификации полей:
  - Марка: `[A-Z][A-Z0-9]*-\d+` (BK1-3, ST2-1, A-7)
  - Кол-во: целое число
  - Размеры: 3-4 значные числа
  - Масса/S: дробные числа

### 5.2 GeneralDataParser (л.1 — Общие данные)

- Извлекает метаданные: номер проекта, объект, стадия
- Извлекает сводную таблицу металлопрофилей (профиль + ГОСТ + масса + марка стали)

---

## 6. API эндпоинты (MVP)

| Метод | Путь | Описание |
|---|---|---|
| POST | `/api/v1/parse/upload` | Загрузка PDF-файла(ов) |
| GET | `/api/v1/parse/batches/{id}` | Статус обработки пакета |
| GET | `/api/v1/parse/batches/{id}/preview` | Предпросмотр распознанных строк |
| POST | `/api/v1/parse/batches/{id}/confirm` | Подтверждение и сохранение в БД |
| GET | `/api/v1/parse/batches/{id}/export/json` | Экспорт в JSON |
| GET | `/api/v1/parse/batches/{id}/export/csv` | Экспорт в CSV |
| GET | `/api/v1/parse/batches/{id}/export/xlsx` | Экспорт в Excel |
| GET | `/api/v1/projects` | Список проектов |
| POST | `/api/v1/projects` | Создать проект |

---

## 7. План развития модулей

### Фаза 1 (MVP) — текущая
- [x] Архитектурный план
- [ ] Parser Engine: KMD Shipping Parser (л.2)
- [ ] General Data Parser (л.1)
- [ ] Database Schema + миграции
- [ ] FastAPI скелет + upload/parse/preview/export
- [ ] Логирование нераспознанных строк

### Фаза 2 — CRM (БП 1.1)
- Модуль клиентов и контрагентов
- Привязка проектов к клиентам
- История взаимодействий

### Фаза 3 — Проектирование (БП 1.2)
- Справочник ОГЗ-составов
- Калькулятор приведённой толщины
- Автоматический подбор состава под REI

### Фаза 4 — Снабжение (БП 1.3)
- Модуль поставщиков и цен
- Автоматический расчёт потребности в материалах
- Формирование заявок на закупку

### Фаза 5 — КП и договоры
- Генератор КП (PDF/DOCX)
- Шаблоны договоров
- График работ
