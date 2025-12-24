from pydantic import BaseModel, Field


class CategoryBase(BaseModel):
    name: str = Field(..., max_length=255, description="Название категории")


class CategoryCreate(BaseModel):
    name: str = Field(..., max_length=255, description="Название категории")


class CategoryRead(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


class CategoryDelete(BaseModel):
    name: str = Field(..., max_length=255, description="Название категории для удаления")
