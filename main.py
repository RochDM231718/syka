from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
import os
from app.routers.admin.auth import router as admin_auth_router
from app.routers.admin.dashboard import router as admin_dashboard_router
from app.routers.admin.users import router as admin_users_router
from app.routers.admin.pages import router as admin_pages_router
from app.routers.admin.achievements import router as admin_achievements_router
from app.routers.admin.moderation import router as admin_moderation_router

from app.middlewares.admin_middleware import GlobalContextMiddleware
from app.infrastructure.tranaslations import TranslationManager

#API routers
from app.routers.api.auth import router as api_auth_router

app = FastAPI()

# ВАЖНО: Сначала добавляем GlobalContextMiddleware (он обернет SessionMiddleware)
# В FastAPI middleware выполняются в порядке "луковицы": последний добавленный - внешний слой.
# Нам нужно, чтобы SessionMiddleware отработал ПЕРВЫМ и создал session,
# а потом GlobalContextMiddleware мог её прочитать.
# Значит, SessionMiddleware должен быть ВНУТРИ GlobalContextMiddleware.
# То есть GlobalContextMiddleware добавляем ПОСЛЕ (если смотреть по коду add_middleware, это "внешний" слой).
# НО! Starlette SessionMiddleware должен быть добавлен ПОСЛЕ нашего middleware, чтобы быть "ближе" к приложению?
# Нет. Порядок add_middleware: первый добавленный - выполняется ПОСЛЕДНИМ на входе и ПЕРВЫМ на выходе.
# Нам нужно: Request -> SessionMiddleware -> GlobalContextMiddleware -> App
# Значит:
# 1. add_middleware(GlobalContextMiddleware)
# 2. add_middleware(SessionMiddleware)

app.add_middleware(GlobalContextMiddleware)
app.add_middleware(SessionMiddleware, secret_key=os.getenv('ADMIN_SECRET_KEY', 'secret'))

app.include_router(admin_auth_router)
app.include_router(admin_dashboard_router)
app.include_router(admin_users_router)
app.include_router(admin_pages_router)
app.include_router(admin_achievements_router)
app.include_router(admin_moderation_router)

app.mount("/static", StaticFiles(directory="static"), name="static")

translation_manager = TranslationManager()

#API routers
app.include_router(api_auth_router)

@app.get('/')
async def welcome():
    return {"message": translation_manager.gettext('welcome_message')}