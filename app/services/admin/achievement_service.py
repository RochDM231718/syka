from typing import List
from fastapi import UploadFile
import shutil
from pathlib import Path
import uuid
import os

from app.repositories.admin.achievement_repository import AchievementRepository
from app.models.achievement import Achievement
from app.models.enums import AchievementStatus
from app.schemas.admin.achievements import AchievementCreate


class AchievementService:
    def __init__(self, repo: AchievementRepository):
        self.repo = repo

    def get_user_achievements(self, user_id: int, page: int = 1):
        return self.repo.get_by_user(user_id, page)

    def create(self, user_id: int, obj_in: AchievementCreate, file: UploadFile):
        # 1. Сохраняем файл
        file_path = self._save_file(file)

        # 2. Создаем объект модели
        achievement_data = {
            "user_id": user_id,
            "title": obj_in.title,
            "description": obj_in.description,
            "file_path": file_path,
            "status": AchievementStatus.PENDING  # Статус по умолчанию "На проверке"
        }

        return self.repo.create(achievement_data)

    def delete(self, id: int, user_id: int):
        # Проверяем, принадлежит ли достижение этому пользователю перед удалением
        achievement = self.repo.find(id)
        if achievement and achievement.user_id == user_id:
            # Здесь можно добавить удаление файла с диска, если нужно
            self.repo.delete(id)
            return True
        return False

    def get_all_pending(self):
        """Возвращает все достижения со статусом PENDING"""
        return self.repo.getDb().query(Achievement).filter(Achievement.status == AchievementStatus.PENDING).all()

    def update_status(self, id: int, status: str):
        """Меняет статус достижения (approved / rejected)"""
        # status приходит как строка из URL, обновляем поле
        self.repo.update(id, {"status": status})

    def _save_file(self, file: UploadFile) -> str:
        upload_dir = Path("static/uploads/achievements")
        upload_dir.mkdir(parents=True, exist_ok=True)

        # Генерируем уникальное имя файла
        file_extension = file.filename.split('.')[-1] if '.' in file.filename else "dat"
        unique_name = f"{uuid.uuid4()}.{file_extension}"
        file_path = upload_dir / unique_name

        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        return f"static/uploads/achievements/{unique_name}"