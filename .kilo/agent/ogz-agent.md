# Agent: OGZ Calculator (Модуль расчёта огнезащиты)

## Назначение
Автоматизировать расчёт приведённой толщины металла и подбор ОГЗ-составов по данным из LineItem. Реализовать API для калькуляции спецификации материалов.

## Контекст
- Проект: UNIK ERP (см. AGENTS.md)
- Основной бизнес компании — огнезащита (ОГЗ) металлоконструкций
- Ключевые параметры: Масса, Площадь поверхности → Приведённая толщина → Состав ОГЗ

## Что уже есть
- `backend/app/models/database.py` — модели:
  - `LineItem` (position, mark, quantity, dims X×Y×Z, unit/total weight, unit/total area)
  - `OgzComposition` (name, composition_type, consumption_rate, price_per_kg)
  - `CommercialOffer` (total_area, total_weight, material_cost, work_cost, total_cost)
  - `SteelProfile` (profile_name, gost_code, steel_grade)
- `backend/app/schemas/parser.py` — `LineItemSchema`
- `backend/app/main.py` — FastAPI app
- `backend/app/config.py` — Settings

## Что нужно сделать

### 1. Создать `backend/app/core/ogz_calculator.py`
- Функция `calculate_reduced_thickness(mass_kg: float, area_m2: float) -> float`
  - Формула: δ = масса / (площадь × 7850) [мм]
  - Учитывать: масса в кг, площадь в м², плотность стали 7850 кг/м³
- Функция `select_ogz_composition(rei_minutes: int, reduced_thickness: float, environment: str) -> dict`
  - Подбор состава по пределу огнестойкости (REI 30/60/90/120/150)
  - Учитывать среду: сухая/влажная/агрессивная
- Функция `calculate_material_consumption(items: list[dict], composition: dict) -> dict`
  - Расход грунта = площадь × норма (кг/м²)
  - Расход краски = площадь × приведённая толщина × норма (кг/м²/мм)
  - Финиш = площадь × норма

### 2. Создать `backend/app/schemas/ogz.py`
- `OgzCalculationRequest` — список line_items + параметры (REI, среда)
- `OgzCalculationResponse` — спецификация: позиции с расходом, итоги, стоимость
- `OgzCompositionSchema` — информация о составе

### 3. Создать `backend/app/services/ogz_service.py`
- `calculate_ogz(items: list[LineItemSchema], rei: int, environment: str) -> OgzCalculationResponse`
- Оркестрация: для каждого item → толщина → состав → расход → умножение на quantity
- Агрегация итогов

### 4. Создать `backend/app/api/routes/ogz.py`
- `POST /api/v1/ogz/calculate` — принимает список item_id + REI, возвращает спецификацию
- `GET /api/v1/ogz/compositions` — справочник составов
- `POST /api/v1/ogz/compositions` — добавить состав
- Зарегистрировать роутер в `app/main.py`

### 5. Заполнить справочник ОГЗ-составов (seed data)
- Создать `backend/scripts/seed_ogz.py`
- Типовые составы для ОГЗ: грунт ГФ-021, краска Термобарьер, финиш ПФ-115
- Расходы: ~0.3 кг/м² грунт, ~0.8-2.5 кг/м²/мм краска

## Выходные файлы (создать новые)
- `backend/app/core/ogz_calculator.py`
- `backend/app/schemas/ogz.py`
- `backend/app/services/ogz_service.py`
- `backend/app/api/routes/ogz.py`
- `backend/scripts/seed_ogz.py`
- Обновление `backend/app/main.py` — добавить ogz_router

## Формулы
- Приведённая толщина: δ_пр = M / (S × ρ), где ρ = 7850 кг/м³
- Расход краски: R = S × δ_пр × N (N — норма расхода кг/м²/мм)
- Стоимость: C = R × P (P — цена за кг)
