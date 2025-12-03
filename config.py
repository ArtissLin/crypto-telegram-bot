import os

class Config:
    # Получаем токен ИЗ ПЕРЕМЕННЫХ ОКРУЖЕНИЯ Railway
    TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
    
    # Если токена нет, покажем ошибку
    if not TELEGRAM_TOKEN:
        print("⚠️  ВНИМАНИЕ: TELEGRAM_TOKEN не найден в переменных окружения!")
        print("💡 Добавьте TELEGRAM_TOKEN в Railway Variables")
    
    @classmethod
    def validate(cls):
        """Проверка наличия обязательных настроек"""
        if not cls.TELEGRAM_TOKEN:
            raise ValueError("❌ TELEGRAM_TOKEN не найден в переменных окружения!")
        return True