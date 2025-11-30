from fastapi import Request, HTTPException, status
import os
from starlette.middleware.base import BaseHTTPMiddleware
from app.infrastructure.database.connection import get_database_connection
from app.models.user import Users
from app.models.achievement import Achievement
from app.models.enums import UserStatus, AchievementStatus


def auth(request: Request):
    if request.session.get('auth_id') is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")


class GlobalContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # 1. Базовые настройки
        app_name = os.getenv("APP_NAME", "Sirius Achievements")
        request.state.app_name = app_name

        # 2. Подсчет счетчиков (только для админ-панели и авторизованных)
        # Мы проверяем наличие сессии, чтобы не нагружать базу лишний раз
        # Но сессия доступна только внутри роутов, а middleware работает ДО них.
        # Поэтому просто проверяем путь /admin

        if request.url.path.startswith("/admin") and not request.url.path.startswith("/admin/static"):
            try:
                db_connection = get_database_connection()
                db = db_connection.get_session()

                # Считаем пользователей на проверке
                pending_users = db.query(Users).filter(Users.status == UserStatus.PENDING).count()
                request.state.pending_users_count = pending_users

                # Считаем достижения на проверке
                pending_achievements = db.query(Achievement).filter(
                    Achievement.status == AchievementStatus.PENDING).count()
                request.state.pending_achievements_count = pending_achievements

                db.close()
            except Exception as e:
                # Если ошибка БД, ставим 0, чтобы сайт не упал
                print(f"Middleware DB Error: {e}")
                request.state.pending_users_count = 0
                request.state.pending_achievements_count = 0
        else:
            request.state.pending_users_count = 0
            request.state.pending_achievements_count = 0

        response = await call_next(request)
        return response