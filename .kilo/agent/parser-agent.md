# Agent: revC04 Parser (KmdMainParser)

## Назначение
Извлечь недостающие ~139 строк из 34-страничного пакета КМД (`testdoc/revC04.pdf`) и заполнить справочник `SteelProfile` данными о профилях металла.

## Контекст
- Проект: UNIK ERP (см. AGENTS.md)
- Л.2 уже распознан на 100% (404 строки через KmdShippingParser)
- revC04 — 34 страницы КМД с таблицами изменений, разбитыми по ревизиям (07-24, 34-24, 136-24, 49-25)
- Из revC04 нужно: (а) дополнительные строки ведомости, (б) привязка Марка → Профиль (двутавр/швеллер/уголок/труба) для таблицы SteelProfile

## Что уже есть
- `backend/app/core/parser_engine.py` — BaseParser (ABC): `extract_text()`, `detect_tables()`, `parse_rows()`, `extract_metadata()`, `validate_row()`, `parse()`
- `backend/app/core/kmd_parser.py` — пример парсера: state-machine разбор строк, regex-паттерны
- `backend/app/models/database.py` — модель `SteelProfile` (profile_name, gost_code, steel_grade, unit_weight_kg, section_type)
- `backend/app/schemas/parser.py` — `LineItemSchema`, `ParseResultSchema`
- `backend/scripts/test_parser.py` — шаблон тестового запуска

## Что нужно сделать

### 1. Изучить revC04.pdf
- Прочитать PDF через pdfplumber (`page.extract_text()`)
- Понять структуру: заголовки ревизий, таблицы с данными, итоговые строки
- Определить паттерны строк (похожи на л.2, но могут отличаться форматом)

### 2. Создать `backend/app/core/revC04_parser.py`
- Класс `RevC04Parser(BaseParser)`
- `extract_text()` — pdfplumber по всем 34 страницам
- `detect_tables()` — найти строки с марками (A-1, BK1-3...) и числовыми данными
- `parse_rows()` — извлечь: position, mark, type_name, quantity, dims, masses, areas
- `extract_metadata()` — номер проекта, ревизии
- Профили стали: двутавр (I), швеллер ([, П), уголок (L), труба (Гн, Тр), круг (O), лист
- На выходе: ParseResultSchema с items (LineItemSchema) + metadata

### 3. Интегрировать с БД
- В `backend/app/services/parsing_service.py` добавить функцию `parse_revC04(file_path) -> ParseResultSchema`
- В `backend/app/api/routes/parser.py` добавить поддержку `parser_type=revC04`

### 4. Протестировать
- Запустить `python backend/scripts/test_parser.py` (или написать отдельный тест)
- Сверить количество извлечённых строк с эталонным Excel
- Проверить, что суммарная масса близка к 263 812 кг

## Выходные файлы (создать новые, существующие не менять без необходимости)
- `backend/app/core/revC04_parser.py` — основной парсер
- Обновление `backend/app/services/parsing_service.py` — функция parse_revC04
- Обновление `backend/app/api/routes/parser.py` — parser_type=revC04

## Ключевые паттерны revC04
- Марка: `[A-Z][A-Z0-9]*-[0-9]+` (BK1-3, ST2-8, A-7)
- Профиль: `I\d{2}[А-Я]\d`, `L\d{2,3}x\d{2,3}`, `\[\d{2,3}[А-Я]`, `Гн\.\d{2,3}`, `O\d{2}`
- Масса: число с десятичной точкой (может быть целым)
- Итоговые строки: «ИТОГО», «ВСЕГО»
