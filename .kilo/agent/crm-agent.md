# Agent: CRM + Frontend (БП 1.1)

## Назначение
Создать модуль CRM (клиенты, проекты) и базовый React-фронтенд с загрузкой PDF и отображением результатов парсинга.

## Контекст
- Проект: UNIK ERP (см. AGENTS.md)
- Стек фронтенда: React + TypeScript + Vite + Ant Design
- Бэкенд уже имеет: API парсинга, API проектов, модели БД

## Что уже есть
- `backend/app/models/database.py` — модели Client, Project, DocumentBatch, LineItem
- `backend/app/api/routes/projects.py` — GET/POST проекты (in-memory, нужно доработать)
- `backend/app/schemas/parser.py` — ProjectCreateSchema, ProjectSchema
- `frontend/src/` — пустая папка

## Что нужно сделать

### 1. Расширить бэкенд CRM
- `POST /api/v1/clients` — создать клиента
- `GET /api/v1/clients` — список клиентов
- `GET /api/v1/clients/{id}` — детали клиента
- Связать Project с Client через client_id
- `GET /api/v1/projects/{id}` — детали проекта (включая batches и line_items)

### 2. Создать React-приложение
- Инициализировать Vite + React + TypeScript в `frontend/`
- Установить Ant Design, React Router, Axios
- Страницы:
  - `/` — Dashboard: список проектов, статусы
  - `/projects/:id` — Детали проекта: загрузка PDF, таблица line_items, экспорт
  - `/projects/new` — Создать проект
  - `/clients` — Список клиентов

### 3. Компоненты
- `ProjectTable` — таблица проектов с фильтрацией
- `LineItemsTable` — таблица строк ведомости (mark, qty, dims, weight, area)
- `PdfUploader` — drag-and-drop загрузка PDF с прогрессом
- `ExportButton` — кнопки экспорта JSON/CSV/XLSX

### 4. Интеграция с API
- Сервис `frontend/src/services/api.ts` — axios-инстанс с baseURL
- Типы `frontend/src/types/` — интерфейсы Project, LineItem, ParseResult

## Выходные файлы

### Бэкенд (новые/обновлённые)
- `backend/app/api/routes/clients.py` — новый роутер
- `backend/app/services/project_service.py` — сервис проектов
- Обновление `backend/app/api/routes/projects.py` — детали проекта
- Обновление `backend/app/main.py` — clients_router

### Фронтенд (все новые)
- `frontend/package.json`
- `frontend/vite.config.ts`
- `frontend/tsconfig.json`
- `frontend/index.html`
- `frontend/src/main.tsx`
- `frontend/src/App.tsx`
- `frontend/src/services/api.ts`
- `frontend/src/types/index.ts`
- `frontend/src/pages/Dashboard.tsx`
- `frontend/src/pages/ProjectDetail.tsx`
- `frontend/src/components/PdfUploader.tsx`
- `frontend/src/components/LineItemsTable.tsx`

## Ключевые правила
1. Все API-ответы: Pydantic-схемы → JSON строго по схемам
2. CORS: разрешён localhost:5173 (Vite dev server)
3. Файлы PDF загружаются через FormData multipart
4. Не менять существующие core-файлы парсера
5. Фронтенд: Ant Design 5.x компоненты, тёмная тема
