import os
import json
import logging

logger = logging.getLogger(__name__)

class Database:
    def __init__(self):
        # Определяем путь к файлу базы данных для Railway
        if os.path.exists('/tmp'):  # Railway использует /tmp
            self.db_path = '/tmp/users_data.json'
        else:
            # Для локальной разработки
            self.db_path = os.path.join(os.path.dirname(__file__), 'users_data.json')
        
        self.data = self._load_data()
        logger.info(f"📁 База данных загружена из: {self.db_path}")
    
    def _load_data(self):
        """Загрузка данных из файла"""
        try:
            if os.path.exists(self.db_path):
                with open(self.db_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.warning(f"Создаю новую базу данных: {e}")
        
        # Возвращаем пустую структуру если файла нет или он пустой
        return {'users': {}}
    
    def _save_data(self):
        """Сохранение данных в файл"""
        try:
            with open(self.db_path, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Ошибка сохранения БД: {e}")
    
    # Добавьте остальные ваши методы ниже...
    # Например: get_user, add_user, add_coin и т.д.