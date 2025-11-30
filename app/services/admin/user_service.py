import uuid
from typing import List
from fastapi import UploadFile
import shutil
from pathlib import Path
from app.schemas.admin.users import UserCreate, UserUpdate, UserOut
from app.schemas.admin.user_tokens import UserTokenCreate, UserTokenType
from app.services.admin.base_crud_service import BaseCrudService, ModelType, CreateSchemaType
from app.services.admin.user_token_service import UserTokenService
from app.repositories.admin.user_repository import UserRepository
from app.repositories.admin.user_token_repository import UserTokenRepository
from app.models.user import Users
from passlib.context import CryptContext
from mailbridge import MailBridge
from app.routers.admin.admin import templates
from starlette.requests import Request
import secrets
import string
import os

bcrypt_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
mailer = MailBridge(provider='smtp',
                    host=os.getenv('MAIL_HOST'),
                    port=os.getenv('MAIL_PORT'),
                    username=os.getenv('MAIL_USERNAME'),
                    password=os.getenv('MAIL_PASSWORD'),
                    use_tls=True,
                    from_email=os.getenv('MAIL_USERNAME')
                    )


class UserService(BaseCrudService[Users, UserCreate, UserUpdate]):
    def __init__(self, repo: UserRepository):
        super().__init__(repo)
        self.request = None

    def set_request(self, request: Request):
        self.request = request

    def get(self, filters: dict = None) -> List[ModelType]:
        users = super().get(filters)
        return [UserOut.model_validate(user) for user in users]

    def create(self, obj_in: CreateSchemaType) -> ModelType:
        result = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(8))
        obj_in.hashed_password = bcrypt_context.hash(result)
        user = self.repository.create(obj_in)
        user_token = self._create_user_token_for_reset_password(user_id=user.id)
        self._send_welcome_email(user, result, user_token)
        return user

    def update_password(self, id: str, password: str):
        self.repository.update_password(id, bcrypt_context.hash(password))

    def save_avatar(self, user_id: int, file: UploadFile) -> str:
        """
    Сохраняет файл аватарки на диск и возвращает путь для сохранения в БД.
    Путь сохранения: static/uploads/avatars/avatar_{user_id}_{uuid}.{ext}
    """
        # 1. Определяем путь к папке загрузок
        upload_dir = Path("static/uploads/avatars")
        upload_dir.mkdir(parents=True, exist_ok=True)

        # 2. Генерируем имя файла: avatar_{user_id}_{random}.{ext}
        filename_parts = file.filename.split('.')
        file_extension = filename_parts[-1] if len(filename_parts) > 1 else "png"

        # Добавляем UUID, чтобы имя файла менялось при каждом обновлении
        unique_code = uuid.uuid4().hex[:8]
        filename = f"avatar_{user_id}_{unique_code}.{file_extension}"
        file_path = upload_dir / filename

        # Удаляем старые аватарки этого пользователя
        for old_file in upload_dir.glob(f"avatar_{user_id}_*"):
            try:
                old_file.unlink()
            except:
                pass

        # 3. Сохраняем файл
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # 4. Возвращаем путь относительно корня проекта (для src в HTML)
        return f"static/uploads/avatars/{filename}"

    def get_pending_users(self):
        """Возвращает пользователей, ожидающих проверки"""
        from app.models.enums import UserStatus
        return self.repository.getDb().query(Users).filter(Users.status == UserStatus.PENDING).all()

    def approve_user(self, user_id: int):
        """Меняет статус на ACTIVE и роль на STUDENT"""
        from app.models.enums import UserStatus, UserRole
        self.repository.update(user_id, {
            "status": UserStatus.ACTIVE,
            "role": UserRole.STUDENT
        })

    def _create_user_token_for_reset_password(self, user_id: int):
        user_token_data = UserTokenCreate(user_id=user_id, type=UserTokenType.RESET_PASSWORD)
        user_token_service = UserTokenService(UserTokenRepository(self.repository.getDb()))
        return user_token_service.create(data=user_token_data)

    def _send_welcome_email(self, user, password: str, user_token):
        template = templates.env.get_template('emails/welcome.html')
        mailer.send(to=user.email,
                    subject="Welcome",
                    body=template.render({
                        'request': self.request,
                        'user': user,
                        'password': password,
                        'url': self.request.url_for('admin.reset-password.form', token=user_token.token)
                    }))