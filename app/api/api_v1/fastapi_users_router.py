from fastapi_users import FastAPIUsers

from core.models import User
from api.dependencies.authentication.user_manager import get_user_manager
from api.dependencies.authentication.backend import authentication_backend

fastapi_users = FastAPIUsers[User, int](
    get_user_manager,
    [authentication_backend],
)

current_super_user = fastapi_users.current_user(superuser=True)