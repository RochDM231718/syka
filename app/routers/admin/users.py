from fastapi import Request, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from typing import Optional
from app.routers.admin.admin import guard_router, templates, get_db
from app.repositories.admin.user_repository import UserRepository
from app.services.admin.user_service import UserService
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.models.enums import UserRole
from app.models.user import Users
from app.schemas.admin.users import UserCreate, UserUpdate

router = guard_router


def get_service(db: Session = Depends(get_db)):
    return UserService(UserRepository(db))


def check_access(request: Request):
    role = request.session.get('auth_role')
    if role not in [UserRole.MODERATOR, UserRole.SUPER_ADMIN]:
        raise HTTPException(status_code=403, detail="Access denied")


# --- API ПОИСКА ---
@router.get('/users/search', response_class=JSONResponse, name='admin.users.search_api')
async def search_users(request: Request, query: str, db: Session = Depends(get_db)):
    check_access(request)
    if not query:
        return []

    users = db.query(Users).filter(
        or_(
            Users.first_name.ilike(f"%{query}%"),
            Users.last_name.ilike(f"%{query}%"),
            Users.email.ilike(f"%{query}%")
        )
    ).limit(5).all()

    return [
        {
            "id": u.id,
            "name": f"{u.first_name} {u.last_name}",
            "email": u.email,
            "avatar": u.avatar_path
        }
        for u in users
    ]


# --- СПИСОК ПОЛЬЗОВАТЕЛЕЙ ---
@router.get('/users', response_class=HTMLResponse, name="admin.users.index")
async def index(
        request: Request,
        query: Optional[str] = "",
        page: Optional[int] = 1,
        service: UserService = Depends(get_service),
        db: Session = Depends(get_db)):
    check_access(request)
    users = service.get({'query': query, 'page': page})

    count_query = db.query(Users)
    if query:
        count_query = count_query.filter(
            or_(
                Users.first_name.ilike(f"%{query}%"),
                Users.last_name.ilike(f"%{query}%"),
                Users.email.ilike(f"%{query}%")
            )
        )
    total_count = count_query.count()

    return templates.TemplateResponse('users/index.html', {
        'request': request,
        'query': query,
        'users': users,
        'total_count': total_count
    })


# --- ПРОСМОТР ПРОФИЛЯ ---
@router.get('/users/{id}', response_class=HTMLResponse, name='admin.users.show')
async def show(id: int, request: Request, service: UserService = Depends(get_service)):
    check_access(request)
    user = service.find(id)

    total_docs = len(user.achievements)

    return templates.TemplateResponse('users/show.html', {
        'request': request,
        'user': user,
        'roles': list(UserRole),
        'achievements': user.achievements,
        'total_docs': total_docs
    })


# --- ОБНОВЛЕНИЕ РОЛИ ---
@router.post('/users/{id}/role', name='admin.users.update_role')
async def update_role(
        id: int,
        request: Request,
        role: str = Form(...),
        service: UserService = Depends(get_service)
):
    if request.session.get('auth_role') != 'super_admin':
        raise HTTPException(status_code=403, detail="Only Super Admin can change roles")

    if id == request.session.get('auth_id'):
        return RedirectResponse(url=request.url_for('admin.users.show', id=id), status_code=302)

    service.repository.update(id, {"role": role})
    return RedirectResponse(url=request.url_for('admin.users.show', id=id), status_code=302)


# --- СОЗДАНИЕ ---
@router.get('/users/create', response_class=HTMLResponse, name='admin.users.create')
async def create(request: Request):
    check_access(request)
    return templates.TemplateResponse('users/create.html', {'request': request, 'roles': list(UserRole)})


@router.post('/users', response_class=HTMLResponse, name='admin.users.store')
async def store(request: Request, db: Session = Depends(get_db), service: UserService = Depends(get_service)):
    check_access(request)
    try:
        form = await request.form()
        form_data = dict(form)
        user_data = UserCreate(**form_data)
        UserCreate.validate_unique_email(user_data.email, db)
        service.set_request(request)
        service.create(user_data)
        return RedirectResponse(url="/admin/users", status_code=302)
    except ValueError as e:
        return templates.TemplateResponse('users/create.html',
                                          {'request': request, 'roles': list(UserRole), 'error_msg': str(e)})


# --- РЕДАКТИРОВАНИЕ (My Profile) ---
@router.get('/users/{id}/edit', response_class=HTMLResponse, name='admin.users.edit')
async def edit(id: int, request: Request, service: UserService = Depends(get_service)):
    if id != request.session.get('auth_id'):
        return RedirectResponse(url=request.url_for('admin.users.show', id=id), status_code=302)

    user = service.find(id)
    total_docs = len(user.achievements)

    return templates.TemplateResponse('users/edit.html', {
        'request': request,
        'roles': list(UserRole),
        'user': user,
        'total_docs': total_docs,
        'achievements': user.achievements  # <-- ДОБАВИЛИ ЭТО
    })


@router.post('/users/{id}', response_class=HTMLResponse, name='admin.users.update')
async def update(
        id: int,
        request: Request,
        db: Session = Depends(get_db),
        service: UserService = Depends(get_service)
):
    if id != request.session.get('auth_id'):
        raise HTTPException(status_code=403, detail="You cannot edit other users.")

    try:
        form = await request.form()
        form_data = dict(form)
        avatar_file = form_data.pop('avatar', None)
        form_data.pop('role', None)

        user_data = UserUpdate(**form_data)

        existing_user = db.query(Users).filter(Users.email == user_data.email).first()
        if existing_user and existing_user.id != id:
            raise ValueError("Email already taken")

        update_payload = user_data.dict(exclude_unset=True)

        if avatar_file and hasattr(avatar_file, 'filename') and avatar_file.filename:
            avatar_path = service.save_avatar(id, avatar_file)
            update_payload["avatar_path"] = avatar_path

        service.repository.update(id, update_payload)

        return RedirectResponse(url="/admin/dashboard", status_code=302)
    except ValueError as e:
        user = service.find(id)
        total_docs = len(user.achievements)
        return templates.TemplateResponse('users/edit.html', {
            'request': request,
            'user': user,
            'roles': list(UserRole),
            'total_docs': total_docs,
            'achievements': user.achievements,  # <-- И ЗДЕСЬ ТОЖЕ
            'error_msg': str(e)
        })


@router.delete('/users/{user_id}', name='admin.users.delete')
async def delete(user_id: int, request: Request, service: UserService = Depends(get_service)):
    check_access(request)
    if user_id != request.session['auth_id']:
        service.delete(user_id)
    else:
        raise HTTPException(status_code=400, detail="You cannot delete yourself.")
    return {"message": 'User has been successfully deleted.'}