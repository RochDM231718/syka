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

    file_path = Column(String, nullable=False)
    preview_path = Column(String, nullable=True)

    status = Column(SQLAlchemyEnum(AchievementStatus), default=AchievementStatus.PENDING)

    # НОВОЕ ПОЛЕ
    rejection_reason = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Связь с пользователем
    user = relationship("Users", back_populates="achievements")