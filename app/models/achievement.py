from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Enum as SQLAlchemyEnum, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.infrastructure.database.connection import Base
from app.models.enums import AchievementStatus


class Achievement(Base):
    __tablename__ = "achievements"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))

    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)

    file_path = Column(String, nullable=False)  # Ссылка на оригинал файла
    preview_path = Column(String, nullable=True)  # Ссылка на превью (если нужно)

    status = Column(SQLAlchemyEnum(AchievementStatus), default=AchievementStatus.PENDING)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Связь с пользователем
    user = relationship("Users", back_populates="achievements")