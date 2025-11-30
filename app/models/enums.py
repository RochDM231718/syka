from enum import Enum

class UserRole(str, Enum):
    GUEST = "guest"             # Только зарегистрировался
    STUDENT = "student"         # Одобренный ученик
    MODERATOR = "moderator"     # Проверяет достижения
    SUPER_ADMIN = "super_admin" # Главный админ

class UserStatus(str, Enum):
    PENDING = "pending"   # На проверке
    ACTIVE = "active"     # Активен
    BANNED = "banned"     # Забанен

class AchievementStatus(str, Enum):
    PENDING = "pending"   # Ждет проверки
    APPROVED = "approved" # Одобрено
    REJECTED = "rejected" # Отклонено

class UserTokenType(str, Enum):
    RESET_PASSWORD = "reset_password"
    EMAIL_VERIFICATION = "email_verification"