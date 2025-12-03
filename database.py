import os
import json
import logging

logger = logging.getLogger(__name__)

class Database:
    def __init__(self):
        # Определяем путь к файлу базы данных для Railway
        if os.path.exists('/tmp'):  # Railway использует /tmp для записи
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
                    data = json.load(f)
                    logger.info(f"✅ Данные успешно загружены")
                    return data
            else:
                logger.info("📝 Файл базы данных не найден, создаю новую")
        except json.JSONDecodeError:
            logger.warning("⚠️ Файл базы данных поврежден, создаю новую")
        except Exception as e:
            logger.error(f"❌ Ошибка при загрузке БД: {e}")
        
        # Возвращаем пустую структуру если файла нет или он поврежден
        return {'users': {}}
    
    def _save_data(self):
        """Сохранение данных в файл"""
        try:
            with open(self.db_path, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
            logger.debug("💾 Данные сохранены")
        except Exception as e:
            logger.error(f"❌ Ошибка сохранения БД: {e}")
    
    def add_user(self, user_id, username):
        """Добавление нового пользователя"""
        user_id_str = str(user_id)
        
        if user_id_str not in self.data['users']:
            self.data['users'][user_id_str] = {
                'username': username,
                'coins': [],  # Список отслеживаемых монет
                'threshold': 1.0,  # Общий порог по умолчанию
                'coin_thresholds': {},  # Индивидуальные пороги для монет
                'last_prices': {}  # Последние известные цены
            }
            self._save_data()
            logger.info(f"👤 Добавлен новый пользователь: {username} ({user_id})")
            return True
        
        logger.debug(f"ℹ️ Пользователь уже существует: {username}")
        return False
    
    def get_user(self, user_id):
        """Получение данных пользователя"""
        user_id_str = str(user_id)
        return self.data['users'].get(user_id_str)
    
    def get_user_coins(self, user_id):
        """Получение списка монет пользователя"""
        user = self.get_user(user_id)
        if user:
            return user.get('coins', [])
        return []
    
    def add_coin(self, user_id, coin_name):
        """Добавление монеты пользователю"""
        user_id_str = str(user_id)
        
        if user_id_str in self.data['users']:
            user = self.data['users'][user_id_str]
            
            if coin_name not in user['coins']:
                user['coins'].append(coin_name)
                self._save_data()
                logger.info(f"✅ Монета '{coin_name}' добавлена пользователю {user_id}")
                return True
            else:
                logger.debug(f"ℹ️ Монета '{coin_name}' уже есть у пользователя {user_id}")
                return False
        
        logger.warning(f"⚠️ Пользователь {user_id} не найден")
        return False
    
    def remove_coin(self, user_id, coin_name):
        """Удаление монеты у пользователя"""
        user_id_str = str(user_id)
        
        if user_id_str in self.data['users']:
            user = self.data['users'][user_id_str]
            
            if coin_name in user['coins']:
                user['coins'].remove(coin_name)
                
                # Удаляем индивидуальный порог если есть
                if coin_name in user.get('coin_thresholds', {}):
                    del user['coin_thresholds'][coin_name]
                
                # Удаляем последнюю цену если есть
                if coin_name in user.get('last_prices', {}):
                    del user['last_prices'][coin_name]
                
                self._save_data()
                logger.info(f"🗑 Монета '{coin_name}' удалена у пользователя {user_id}")
                return True
        
        return False
    
    def set_threshold(self, user_id, threshold):
        """Установка общего порога для пользователя"""
        user_id_str = str(user_id)
        
        if user_id_str in self.data['users']:
            self.data['users'][user_id_str]['threshold'] = float(threshold)
            self._save_data()
            logger.info(f"⚙️ Общий порог установлен: {threshold}% для {user_id}")
            return True
        
        return False
    
    def set_coin_threshold(self, user_id, coin_name, threshold):
        """Установка индивидуального порога для монеты"""
        user_id_str = str(user_id)
        
        if user_id_str in self.data['users']:
            user = self.data['users'][user_id_str]
            
            # Создаем словарь если его нет
            if 'coin_thresholds' not in user:
                user['coin_thresholds'] = {}
            
            user['coin_thresholds'][coin_name] = float(threshold)
            self._save_data()
            logger.info(f"🔸 Индивидуальный порог для {coin_name}: {threshold}%")
            return True
        
        return False
    
    def get_coin_threshold(self, user_id, coin_name):
        """Получение порога для монеты (индивидуальный или общий)"""
        user = self.get_user(user_id)
        if not user:
            return 1.0  # Значение по умолчанию
        
        # Проверяем индивидуальный порог
        if coin_name in user.get('coin_thresholds', {}):
            return user['coin_thresholds'][coin_name]
        
        # Возвращаем общий порог
        return user.get('threshold', 1.0)
    
    def update_price(self, user_id, coin_name, price):
        """Обновление последней известной цены"""
        user_id_str = str(user_id)
        
        if user_id_str in self.data['users']:
            user = self.data['users'][user_id_str]
            
            # Создаем словарь если его нет
            if 'last_prices' not in user:
                user['last_prices'] = {}
            
            user['last_prices'][coin_name] = float(price)
            self._save_data()
            logger.debug(f"💰 Обновлена цена {coin_name}: ${price}")
            return True
        
        return False
    
    def get_last_price(self, user_id, coin_name):
        """Получение последней известной цены"""
        user = self.get_user(user_id)
        if user and coin_name in user.get('last_prices', {}):
            return user['last_prices'][coin_name]
        return None
    
    def get_all_users(self):
        """Получение списка всех пользователей"""
        return list(self.data['users'].keys())
    
    def has_coin(self, user_id, coin_name):
        """Проверка, есть ли у пользователя монета"""
        user = self.get_user(user_id)
        if user:
            return coin_name in user.get('coins', [])
        return False
    
    def remove_individual_threshold(self, user_id, coin_name):
        """Удаление индивидуального порога"""
        user_id_str = str(user_id)
        
        if user_id_str in self.data['users']:
            user = self.data['users'][user_id_str]
            
            if 'coin_thresholds' in user and coin_name in user['coin_thresholds']:
                del user['coin_thresholds'][coin_name]
                self._save_data()
                logger.info(f"🗑 Удален инд. порог для {coin_name}")
                return True
        
        return False
    
    def clear_user_data(self, user_id):
        """Очистка всех данных пользователя"""
        user_id_str = str(user_id)
        
        if user_id_str in self.data['users']:
            del self.data['users'][user_id_str]
            self._save_data()
            logger.info(f"🧹 Данные пользователя {user_id} очищены")
            return True
        
        return False

# Создаем глобальный объект базы данных
db = Database()