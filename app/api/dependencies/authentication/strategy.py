from typing import TYPE_CHECKING

from fastapi import Depends
from fastapi_users.authentication.strategy.db import (
    AccessTokenDatabase,
    DatabaseStrategy,
)

from core.config import settings
from .access_tokens import get_access_tokens_db

if TYPE_CHECKING:
    from core.models import AccessToken


def get_database_strategy(
    access_tokens_db: AccessTokenDatabase["AccessToken"] = Depends(get_access_tokens_db),
) -> DatabaseStrategy:
    return DatabaseStrategy(
        database=access_tokens_db,
        lifetime_seconds=settings.access_token.lifetime_seconds,
    )