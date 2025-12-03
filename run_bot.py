import asyncio
import logging
from threading import Thread
from bot import main as run_bot
from price_checker import PriceChecker
from telegram.ext import Application
from config import Config

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def run_price_checker(application):
    """Запускает проверку цен в отдельном потоке"""
    async def checker_loop():
        price_checker = PriceChecker(application)
        await price_checker.run_periodically(interval_seconds=60)  # Проверка каждую минуту
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(checker_loop())

def main():
    """Запускает и бота, и проверку цен"""
    if not Config.TELEGRAM_TOKEN:
        logger.error("❌ ОШИБКА: TELEGRAM_TOKEN не найден!")
        return
    
    try:
        # Создаем Application для бота
        application = Application.builder().token(Config.TELEGRAM_TOKEN).build()
        
        # Запускаем проверку цен в отдельном потоке
        checker_thread = Thread(target=run_price_checker, args=(application,), daemon=True)
        checker_thread.start()
        
        logger.info("✅ Запущена проверка цен (каждую минуту)")
        
        # Импортируем и регистрируем обработчики команд
        from bot import (
            start, add_coin_command, list_coins_command, 
            threshold_command, help_command, handle_message
        )
        from telegram.ext import CommandHandler, MessageHandler, filters
        
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("add", add_coin_command))
        application.add_handler(CommandHandler("list", list_coins_command))
        application.add_handler(CommandHandler("threshold", threshold_command))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        
        # Запускаем бота
        logger.info("🤖 Бот запущен...")
        logger.info("📱 Откройте Telegram и найдите своего бота")
        logger.info("💬 Напишите /start чтобы начать")
        
        application.run_polling()
        
    except Exception as e:
        logger.error(f"❌ Ошибка при запуске: {e}")

if __name__ == '__main__':
    main()