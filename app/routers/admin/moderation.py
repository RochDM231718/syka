from fastapi import Request, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from app.routers.admin.admin import guard_router, templates, get_db
from app.repositories.admin.user_repository import UserRepository
from app.services.admin.user_service import UserService
from app.repositories.admin.achievement_repository import AchievementRepository
from app.services.admin.achievement_service import AchievementService
from app.models.user import Users
from app.models.enums import UserRole, AchievementStatus

router = guard_router


def get_user_service(db: Session = Depends(get_db)):
    return UserService(UserRepository(db))


def get_achievement_service(db: Session = Depends(get_db)):
    return AchievementService(AchievementRepository(db))


# Проверка прав: пускаем только Модераторов и Супер-админов
async def ensure_moderator(request: Request, db: Session = Depends(get_db)):
    user_id = request.session.get('auth_id')
    if not user_id:
        raise HTTPException(status_code=403, detail="Not authenticated")

    user = db.query(Users).get(user_id)
    if not user:
        raise HTTPException(status_code=403, detail="User not found")

    # Разрешаем доступ Супер-админу и Модератору
    if user.role not in [UserRole.MODERATOR, UserRole.SUPER_ADMIN]:
        raise HTTPException(status_code=403, detail="Access denied: Moderators only")
    return user


# --- Управление пользователями ---

@router.get('/moderation/users', response_class=HTMLResponse, name='admin.moderation.users')
async def pending_users(
        request: Request,
        service: UserService = Depends(get_user_service),
        admin=Depends(ensure_moderator)
):
    users = service.get_pending_users()
    return templates.TemplateResponse('moderation/users.html', {'request': request, 'users': users})


@router.post('/moderation/users/{id}/approve', name='admin.moderation.users.approve')
async def approve_user(
        id: int,
        request: Request,
        service: UserService = Depends(get_user_service),
        admin=Depends(ensure_moderator)
):
    service.approve_user(id)
    return RedirectResponse(url="/admin/moderation/users", status_code=302)


# --- Управление достижениями ---

@router.get('/moderation/achievements', response_class=HTMLResponse, name='admin.moderation.achievements')
async def pending_achievements(
        request: Request,
        service: AchievementService = Depends(get_achievement_service),
        admin=Depends(ensure_moderator)
):
    achievements = service.get_all_pending()
    return templates.TemplateResponse('moderation/achievements.html',
                                      {'request': request, 'achievements': achievements})


@router.post('/moderation/achievements/{id}/{status}', name='admin.moderation.achievements.update')
async def set_achievement_status(
        id: int,
        status: str,
        request: Request,
        service: AchievementService = Depends(get_achievement_service),
        admin=Depends(ensure_moderator)
):
    # status может быть 'approved' или 'rejected'
    service.update_status(id, status)
    return RedirectResponse(url="/admin/moderation/achievements", status_code=302)