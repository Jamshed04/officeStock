from pydantic import BaseModel, Field


class CategoryBase(BaseModel):
    """Базовая схема категории"""
    name: str = Field(..., max_length=255, description="Название категории")


class CategoryCreate(BaseModel):
    """Схема для создания категории"""
    name: str = Field(..., max_length=255, description="Название категории")


class CategoryRead(BaseModel):
    """Схема для чтения категории"""
    id: int
    name: str

    class Config:
        from_attributes = True


class CategoryDelete(BaseModel):
    """Схема для удаления категории"""
    name: str = Field(..., max_length=255, description="Название категории для удаления")
