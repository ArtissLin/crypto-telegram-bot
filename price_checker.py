import asyncio
import logging
from datetime import datetime
from crypto_api import crypto_api
from database import db

logger = logging.getLogger(__name__)

class PriceChecker:
    """Класс для проверки изменения цен"""
    
    def __init__(self, application):
        self.application = application
        self.running = False
        
    async def check_prices(self):
        """Проверяет цены для всех отслеживаемых монет"""
        try:
            # Получаем все уникальные монеты
            all_coins = db.get_all_users_coins()
            
            if not all_coins:
                logger.debug("Нет монет для проверки")
                return
            
            logger.info(f"Проверяем цены для {len(all_coins)} монет: {', '.join(all_coins[:5])}...")
            
            # Получаем текущие цены
            current_prices = crypto_api.get_multiple_prices(all_coins)
            
            if not current_prices:
                logger.warning("Не удалось получить цены")
                return
            
            # Проверяем изменения для каждого пользователя
            for coin_name, current_price in current_prices.items():
                await self.check_coin_price(coin_name, current_price)
                
        except Exception as e:
            logger.error(f"Ошибка при проверке цен: {e}")
    
    async def check_coin_price(self, coin_name: str, current_price: float):
        """Проверяет изменение цены для конкретной монеты"""
        users = db.get_users_for_coin(coin_name)
        
        for user_info in users:
            user_id = user_info['user_id']
            threshold = user_info['threshold']
            last_price = user_info['last_price']
            
            # Если это первая проверка - просто сохраняем цену
            if last_price is None:
                db.update_price(user_id, coin_name, current_price)
                continue
            
            # Вычисляем процент изменения
            price_change = abs((current_price - last_price) / last_price * 100)
            
            # Если изменение превышает порог - отправляем уведомление
            if price_change >= threshold:
                await self.send_notification(
                    user_id, 
                    coin_name, 
                    last_price, 
                    current_price, 
                    price_change
                )
                
                # Обновляем последнюю цену
                db.update_price(user_id, coin_name, current_price)
    
    async def send_notification(self, user_id: int, coin_name: str, 
                               old_price: float, new_price: float, 
                               change_percent: float):
        """Отправляет уведомление пользователю"""
        try:
            # Определяем направление изменения
            if new_price > old_price:
                direction = "📈 РОСТ"
                emoji = "🟢"
            else:
                direction = "📉 ПАДЕНИЕ"
                emoji = "🔴"
            
            # Форматируем сообщение
            message = (
                f"{emoji} *УВЕДОМЛЕНИЕ О ЦЕНЕ*\n\n"
                f"*Монета:* {coin_name.upper()}\n"
                f"*Изменение:* {direction}\n"
                f"*Процент:* {change_percent:.2f}%\n\n"
                f"*Было:* ${old_price:.4f}\n"
                f"*Стало:* ${new_price:.4f}\n"
                f"*Разница:* ${abs(new_price - old_price):.4f}\n\n"
                f"_Время: {datetime.now().strftime('%H:%M:%S')}_"
            )
            
            # Отправляем сообщение
            await self.application.bot.send_message(
                chat_id=user_id,
                text=message,
                parse_mode='Markdown'
            )
            
            logger.info(f"Отправлено уведомление пользователю {user_id} о {coin_name} ({change_percent:.2f}%)")
            
        except Exception as e:
            logger.error(f"Ошибка при отправке уведомления пользователю {user_id}: {e}")
    
    async def run_periodically(self, interval_seconds: int = 60):
        """Запускает периодическую проверку цен"""
        self.running = True
        logger.info(f"Запущена периодическая проверка цен (интервал: {interval_seconds} сек)")
        
        while self.running:
            try:
                await self.check_prices()
            except Exception as e:
                logger.error(f"Ошибка в основном цикле проверки: {e}")
            
            # Ждем перед следующей проверкой
            await asyncio.sleep(interval_seconds)
    
    def stop(self):
        """Останавливает проверку цен"""
        self.running = False
        logger.info("Проверка цен остановлена")