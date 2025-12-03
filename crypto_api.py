import requests
import logging
from typing import Optional, Dict

logger = logging.getLogger(__name__)

class CryptoAPI:
    """Класс для работы с API криптовалют"""
    
    def __init__(self):
        self.base_url = "https://api.coingecko.com/api/v3"
        
    def get_price(self, coin_id: str) -> Optional[float]:
        """
        Получает текущую цену криптовалюты в USD
        
        Args:
            coin_id: ID монеты (например: 'bitcoin', 'ethereum')
        
        Returns:
            Цена в USD или None при ошибке
        """
        try:
            # Приводим к нижнему регистру
            coin_id = coin_id.lower()
            
            url = f"{self.base_url}/simple/price"
            params = {
                'ids': coin_id,
                'vs_currencies': 'usd'
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if coin_id in data and 'usd' in data[coin_id]:
                price = data[coin_id]['usd']
                logger.debug(f"Цена {coin_id}: ${price}")
                return price
            else:
                logger.warning(f"Монета {coin_id} не найдена в ответе API")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка при запросе цены для {coin_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"Неожиданная ошибка для {coin_id}: {e}")
            return None
    
    def get_multiple_prices(self, coin_ids: list) -> Dict[str, float]:
        """
        Получает цены для нескольких монет одновременно
        
        Args:
            coin_ids: список ID монет
        
        Returns:
            Словарь {coin_id: цена}
        """
        if not coin_ids:
            return {}
            
        try:
            # Приводим все к нижнему регистру
            coin_ids = [coin_id.lower() for coin_id in coin_ids]
            
            url = f"{self.base_url}/simple/price"
            params = {
                'ids': ','.join(coin_ids),
                'vs_currencies': 'usd'
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            prices = {}
            for coin_id in coin_ids:
                if coin_id in data and 'usd' in data[coin_id]:
                    prices[coin_id] = data[coin_id]['usd']
                else:
                    logger.warning(f"Монета {coin_id} не найдена")
                    
            return prices
            
        except Exception as e:
            logger.error(f"Ошибка при запросе цен: {e}")
            return {}
    
    def check_coin_exists(self, coin_id: str) -> bool:
        """
        Проверяет, существует ли монета в API
        
        Args:
            coin_id: ID монеты для проверки
        
        Returns:
            True если монета существует
        """
        # Просто пытаемся получить цену - если получили, значит монета существует
        price = self.get_price(coin_id)
        return price is not None

# Создаем глобальный объект API
crypto_api = CryptoAPI()