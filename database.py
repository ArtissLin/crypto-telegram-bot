import json
import os

DB_FILE = 'users_data.json'

class Database:
   def __init__(self):
    # Определяем путь к файлу базы данных для Railway
    if os.path.exists('/tmp'):  # Railway использует /tmp
        self.db_path = '/tmp/users_data.json'
    else:
        # Для локальной разработки
        self.db_path = os.path.join(os.path.dirname(__file__), 'users_data.json')
    
    self.data = self._load_data()
    print(f"📁 База данных загружена из: {self.db_path}")
    def __init__(self):
        self.data = self._load_data()
    
    def _load_data(self):
        """Загружаем данные из файла"""
        if os.path.exists(DB_FILE):
            try:
                with open(DB_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def _save_data(self):
        """Сохраняем данные в файл"""
        with open(DB_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)
    
    def add_user(self, user_id: int, username: str = ""):
        """Добавляем нового пользователя"""
        user_id_str = str(user_id)
        if user_id_str not in self.data:
            self.data[user_id_str] = {
                'username': username,
                'coins': [],  # список монет
                'threshold': 1.0,  # общий порог по умолчанию
                'coin_thresholds': {},  # индивидуальные пороги для монет
                'last_prices': {}  # последние цены
            }
            self._save_data()
    
    def add_coin(self, user_id: int, coin_name: str):
        """Добавляем монету для отслеживания"""
        user_id_str = str(user_id)
        if user_id_str in self.data:
            if coin_name not in self.data[user_id_str]['coins']:
                self.data[user_id_str]['coins'].append(coin_name)
                self._save_data()
                return True
        return False
    
    def get_user_coins(self, user_id: int):
        """Получаем список монет пользователя"""
        user_id_str = str(user_id)
        if user_id_str in self.data:
            return self.data[user_id_str]['coins']
        return []
    
    def get_user(self, user_id: int):
        """Получаем данные пользователя"""
        user_id_str = str(user_id)
        return self.data.get(user_id_str)
    
    def set_threshold(self, user_id: int, threshold: float):
        """Устанавливаем общий порог уведомлений"""
        user_id_str = str(user_id)
        if user_id_str in self.data:
            self.data[user_id_str]['threshold'] = threshold
            self._save_data()
            return True
        return False
    
    def set_coin_threshold(self, user_id: int, coin_name: str, threshold: float):
        """Устанавливаем индивидуальный порог для конкретной монеты"""
        user_id_str = str(user_id)
        if user_id_str in self.data and coin_name in self.data[user_id_str]['coins']:
            # Создаем словарь coin_thresholds если его нет
            if 'coin_thresholds' not in self.data[user_id_str]:
                self.data[user_id_str]['coin_thresholds'] = {}
            
            self.data[user_id_str]['coin_thresholds'][coin_name] = threshold
            self._save_data()
            return True
        return False
    
    def get_coin_threshold(self, user_id: int, coin_name: str):
        """Получаем порог для монеты"""
        user_id_str = str(user_id)
        if user_id_str in self.data:
            # Проверяем индивидуальный порог
            coin_thresholds = self.data[user_id_str].get('coin_thresholds', {})
            if coin_name in coin_thresholds:
                return coin_thresholds[coin_name]
            
            # Если нет индивидуального - возвращаем общий порог
            return self.data[user_id_str].get('threshold', 1.0)
        
        return 1.0  # значение по умолчанию
    
    def get_all_coin_thresholds(self, user_id: int):
        """Получаем все индивидуальные пороги пользователя"""
        user_id_str = str(user_id)
        if user_id_str in self.data:
            return self.data[user_id_str].get('coin_thresholds', {})
        return {}
    
    def get_all_users_coins(self):
        """Получаем все уникальные монеты всех пользователей"""
        all_coins = set()
        for user_data in self.data.values():
            all_coins.update(user_data.get('coins', []))
        return list(all_coins)
    
    def get_users_for_coin(self, coin_name: str):
        """Получаем список пользователей, которые отслеживают эту монету"""
        users = []
        for user_id_str, user_data in self.data.items():
            if coin_name in user_data.get('coins', []):
                # Получаем порог для этой монеты
                threshold = 1.0
                coin_thresholds = user_data.get('coin_thresholds', {})
                if coin_name in coin_thresholds:
                    threshold = coin_thresholds[coin_name]
                elif 'threshold' in user_data:
                    threshold = user_data['threshold']
                
                users.append({
                    'user_id': int(user_id_str),
                    'threshold': threshold,
                    'last_price': user_data.get('last_prices', {}).get(coin_name)
                })
        return users
    
    def update_price(self, user_id: int, coin_name: str, price: float):
        """Обновляем последнюю цену для монеты пользователя"""
        user_id_str = str(user_id)
        if user_id_str in self.data:
            # Создаем словарь last_prices если его нет
            if 'last_prices' not in self.data[user_id_str]:
                self.data[user_id_str]['last_prices'] = {}
            
            self.data[user_id_str]['last_prices'][coin_name] = price
            self._save_data()
    
    def remove_coin(self, user_id: int, coin_name: str):
        """Удаляем монету из списка пользователя"""
        user_id_str = str(user_id)
        if user_id_str in self.data and coin_name in self.data[user_id_str]['coins']:
            # Удаляем монету из списка
            self.data[user_id_str]['coins'].remove(coin_name)
            
            # Удаляем индивидуальный порог если есть
            coin_thresholds = self.data[user_id_str].get('coin_thresholds', {})
            if coin_name in coin_thresholds:
                del coin_thresholds[coin_name]
            
            # Удаляем последнюю цену если есть
            last_prices = self.data[user_id_str].get('last_prices', {})
            if coin_name in last_prices:
                del last_prices[coin_name]
            
            self._save_data()
            return True
        return False

# Создаем глобальный объект базы данных
db = Database()