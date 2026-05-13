from pydantic import BaseModel, Field
from typing import Optional
from decimal import Decimal
from uuid import UUID


class OgzCompositionSchema(BaseModel):
    """Справочная запись ОГЗ-состава."""
    id: Optional[UUID] = None
    name: str
    composition_type: str  # grunt | kraska | finish
    consumption_rate: Optional[Decimal] = None
    price_per_kg: Optional[Decimal] = None
    dry_residue: Optional[Decimal] = None
    density: Optional[Decimal] = None
    min_ptm_mm: Optional[Decimal] = None
    max_ptm_mm: Optional[Decimal] = None
    rei_minutes: Optional[int] = None
    environment: Optional[str] = None

    model_config = {"from_attributes": True}


class OgzLineItemInput(BaseModel):
    """Входные данные по строке ведомости для расчёта ОГЗ."""
    line_item_id: Optional[UUID] = None
    mark: Optional[str] = None
    type_name: Optional[str] = None
    quantity: Decimal = Decimal("1")
    unit_weight_kg: Optional[Decimal] = None
    total_weight_kg: Optional[Decimal] = None
    unit_area_m2: Optional[Decimal] = None
    total_area_m2: Optional[Decimal] = None
    ptm: Optional[Decimal] = None


class OgzCalculationRequest(BaseModel):
    """Запрос на расчёт ОГЗ."""
    items: list[OgzLineItemInput] = Field(default_factory=list)
    line_item_ids: list[UUID] = Field(default_factory=list)
    rei: int = Field(ge=15, le=240, description="Предел огнестойкости, мин")
    environment: str | None = Field(default=None, description="Среда: сухая / влажная / агрессивная. Если не указана — из настроек админа.")


class OgzPositionResult(BaseModel):
    """Результат расчёта по одной позиции."""
    mark: Optional[str] = None
    type_name: Optional[str] = None
    quantity: int = 1
    unit_weight_kg: float = 0.0
    unit_area_m2: float = 0.0
    reduced_thickness_mm: float = 0.0
    matched_composition_id: Optional[str] = None
    matched_composition_name: Optional[str] = None
    grunt_consumption_kg: float = 0.0
    kraska_consumption_kg: float = 0.0
    finish_consumption_kg: float = 0.0
    position_cost_rub: float = 0.0
    verification_warnings: list[str] = Field(default_factory=list)


class OgzCompositionInfo(BaseModel):
    """Информация о подобранном составе."""
    rei_minutes: int
    environment: str
    grunt_name: str
    grunt_rate_kgm2: float
    grunt_price_per_kg: float
    grunt_dry_residue: Optional[float] = None
    grunt_density: Optional[float] = None
    kraska_name: str
    kraska_rate_kgm2mm: float
    kraska_price_per_kg: float
    kraska_dry_residue: Optional[float] = None
    kraska_density: Optional[float] = None
    finish_name: str
    finish_rate_kgm2: float
    finish_price_per_kg: float
    finish_dry_residue: Optional[float] = None
    finish_density: Optional[float] = None


class OgzCalculationTotals(BaseModel):
    """Итоговые показатели расчёта."""
    total_quantity: int = 0
    total_weight_kg: float = 0.0
    total_area_m2: float = 0.0
    grunt_consumption_kg: float = 0.0
    kraska_consumption_kg: float = 0.0
    finish_consumption_kg: float = 0.0
    total_material_cost_rub: float = 0.0


class OgzCalculationResponse(BaseModel):
    """Ответ API: полная спецификация ОГЗ."""
    positions: list[OgzPositionResult] = Field(default_factory=list)
    totals: OgzCalculationTotals = Field(default_factory=OgzCalculationTotals)
    composition: Optional[OgzCompositionInfo] = None
    errors: list[str] = Field(default_factory=list)


class OgzCompositionCreateRequest(BaseModel):
    """Запрос на создание состава в справочнике."""
    name: str
    composition_type: str
    consumption_rate: Optional[Decimal] = None
    price_per_kg: Optional[Decimal] = None
    dry_residue: Optional[Decimal] = None
    density: Optional[Decimal] = None
    min_ptm_mm: Optional[Decimal] = None
    max_ptm_mm: Optional[Decimal] = None
    rei_minutes: Optional[int] = None
    environment: Optional[str] = None
