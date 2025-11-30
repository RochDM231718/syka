from sqlalchemy import Column, Integer, String, Boolean, Enum as SQLAlchemyEnum
from sqlalchemy.orm import relationship
from app.infrastructure.database.connection import Base
from app.models.enums import UserRole, UserStatus

# ВАЖНО: Импортируем Achievement, чтобы SQLAlchemy знала об этой модели
# (Используем строковый импорт внутри, если боимся циклов, но здесь это безопасно)
import app.models.achievement


class Users(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    first_name = Column(String)
    last_name = Column(String)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)

    role = Column(SQLAlchemyEnum(UserRole), default=UserRole.GUEST)
    status = Column(SQLAlchemyEnum(UserStatus), default=UserStatus.PENDING)
    avatar_path = Column(String, nullable=True)

    achievements = relationship("Achievement", back_populates="user")