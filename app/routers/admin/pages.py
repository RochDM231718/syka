from fastapi import Request, Depends, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.routers.admin.admin import guard_router, templates, get_db
from app.models.achievement import Achievement
from app.models.user import Users
from app.models.enums import UserRole

router = guard_router


# Проверка прав (только модераторы и админы видят все документы)
def check_access(request: Request):
    role = request.session.get('auth_role')
    if role not in [UserRole.MODERATOR, UserRole.SUPER_ADMIN]:
        raise HTTPException(status_code=403, detail="Access denied")


# --- API ПОИСКА ДОКУМЕНТОВ ---
@router.get('/pages/search', response_class=JSONResponse, name='admin.pages.search_api')
async def search_documents(request: Request, query: str, db: Session = Depends(get_db)):
    check_access(request)
    if not query:
        return []

    # Ищем по названию документа ИЛИ по имени студента
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
            "id": doc.user_id,  # Ведем на профиль пользователя
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

    # Базовый запрос
    sql_query = db.query(Achievement).join(Users).order_by(Achievement.created_at.desc())

    # Фильтрация если есть query из формы (обычный поиск без JS)
    if query:
        sql_query = sql_query.filter(
            or_(
                Achievement.title.ilike(f"%{query}%"),
                Users.first_name.ilike(f"%{query}%"),
                Users.last_name.ilike(f"%{query}%")
            )
        )

    documents = sql_query.limit(50).all()  # Ограничим 50 последних

    return templates.TemplateResponse('pages/index.html', {
        'request': request,
        'query': query,
        'documents': documents
    })