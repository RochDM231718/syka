from fastapi import Request, HTTPException, status
import os
from starlette.middleware.base import BaseHTTPMiddleware
from app.infrastructure.database.connection import get_database_connection
from app.models.user import Users
from app.models.achievement import Achievement
from app.models.enums import UserStatus, AchievementStatus

from app.infrastructure.tranaslations import current_locale


def auth(request: Request):
    if request.session.get('auth_id') is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")


class GlobalContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):

        locale = request.session.get('locale', 'en')
        token = current_locale.set(locale)

        app_name = os.getenv("APP_NAME", "Sirius Achievements")
        request.state.app_name = app_name

        if request.url.path.startswith("/admin") and not request.url.path.startswith("/admin/static"):
            try:
                db_connection = get_database_connection()
                db = db_connection.get_session()

                pending_users = db.query(Users).filter(Users.status == UserStatus.PENDING).count()
                request.state.pending_users_count = pending_users

                pending_achievements = db.query(Achievement).filter(
                    Achievement.status == AchievementStatus.PENDING).count()
                request.state.pending_achievements_count = pending_achievements

                db.close()
            except Exception as e:
                print(f"Middleware DB Error: {e}")
                request.state.pending_users_count = 0
                request.state.pending_achievements_count = 0
        else:
            request.state.pending_users_count = 0
            request.state.pending_achievements_count = 0

        response = await call_next(request)

        current_locale.reset(token)

        return response