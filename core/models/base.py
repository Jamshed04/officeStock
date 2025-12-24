from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import declared_attr

from core.config import settings
from utils import camel_case_to_snake_case


class Base(DeclarativeBase):
    __abstract__ = True

    meta = MetaData(
        naming_convention=settings.db.naming_convention
    )

    @declared_attr.directive
    def __tablename__(cls) -> str:
        name = camel_case_to_snake_case(cls.__name__)
        if name.endswith("y"):
            name = name[:-1] + "ies"
        elif name.endswith("s"):
            name += "es"
        else:
            name += "s"
        return name
