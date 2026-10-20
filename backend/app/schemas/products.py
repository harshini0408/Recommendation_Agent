from pydantic import BaseModel, ConfigDict, Field


class ProductOut(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")
    id: str
    name: str
    category: str
    price_inr: int = Field(gt=0)
    cpu_label: str
    cpu_tier: int = Field(ge=1, le=5)
    ram_gb: int = Field(gt=0)
    storage_gb: int = Field(gt=0)
    storage_type: str
    gpu_label: str
    gpu_tier: int = Field(ge=0, le=5)
    dedicated_gpu: bool | None
    vram_gb: int | None = Field(ge=0)
    weight_kg: float | None = Field(gt=0)
    battery_hours: float | None = Field(gt=0)
    use_case_tags: list[str]
    feature_tags: list[str]
    is_synthetic: bool


class ProductPage(BaseModel):
    items: list[ProductOut]
    total: int
    page: int
    page_size: int
