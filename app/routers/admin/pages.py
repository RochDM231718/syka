from fastapi import Request, Depends, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.routers.admin.admin import guard_router, templates, get_db
from app.models.achievement import Achievement
from app.models.user import Users
from app.models.enums import UserRole
from app.services.admin.achievement_service import AchievementService
from app.repositories.admin.achievement_repository import AchievementRepository

router = guard_router


def get_achievement_service(db: Session = Depends(get_db)):
    return AchievementService(AchievementRepository(db))


def check_access(request: Request):
    role = request.session.get('auth_role')
    if role not in [UserRole.MODERATOR, UserRole.SUPER_ADMIN]:
        raise HTTPException(status_code=403, detail="Access denied")


# --- API ПОИСКА ---
@router.get('/pages/search', response_class=JSONResponse, name='admin.pages.search_api')
async def search_documents(request: Request, query: str, db: Session = Depends(get_db)):
    check_access(request)
    if not query:
        return []

    documents = db.query(Achievement).join(Users).filter(
        or_(
            Achievement.title.ilike(f"%{query}%"),
            Users.first_name.ilike(f"%{query}%"),
            Users.last_name.ilike(f"%{query}%"),
            Users.email.ilike(f"%{query}%")
        )
    ).limit(10).all()

    return [
        {
            "id": doc.user_id,
            "title": doc.title,
            "user": f"{doc.user.first_name} {doc.user.last_name}",
            "status": doc.status.value
        }
        for doc in documents
    ]


# --- СПИСОК ВСЕХ ДОКУМЕНТОВ ---
@router.get('/pages', response_class=HTMLResponse, name="admin.pages.index")
async def index(
        request: Request,
        query: str = "",
        db: Session = Depends(get_db)
):
    check_access(request)

    # 1. Формируем Базовый Запрос (ОБЯЗАТЕЛЬНО c JOIN Users)
    # Это отфильтрует достижения удаленных пользователей
    base_query = db.query(Achievement).join(Users)

    # 2. Применяем фильтры поиска
    if query:
        base_query = base_query.filter(
            or_(
                Achievement.title.ilike(f"%{query}%"),
                Users.first_name.ilike(f"%{query}%"),
                Users.last_name.ilike(f"%{query}%")
            )
        )

    # 3. Считаем количество ДО применения лимитов
    total_count = base_query.count()

    # 4. Получаем данные для таблицы (сортировка + лимит)
    documents = base_query.order_by(Achievement.created_at.desc()).limit(50).all()

    return templates.TemplateResponse('pages/index.html', {
        'request': request,
        'query': query,
        'documents': documents,
        'total_count': total_count  # Теперь цифра будет совпадать с реальностью
    })


# --- УДАЛЕНИЕ ---
@router.post('/pages/{id}/delete', name='admin.pages.delete')
async def delete_document(
        id: int,
        request: Request,
        service: AchievementService = Depends(get_achievement_service)
):
    check_access(request)

    user_id = request.session['auth_id']
    user_role = request.session.get('auth_role')

    service.delete(id, user_id, user_role)

    return RedirectResponse(url="/admin/pages", status_code=302)