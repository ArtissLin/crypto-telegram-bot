import logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext, CallbackQueryHandler
from config import Config
from database import db
from crypto_api import crypto_api

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ========== КНОПОЧНЫЕ МЕНЮ ==========

def get_main_menu():
    """Главное меню"""
    keyboard = [
        [InlineKeyboardButton("➕ Добавить монету", callback_data='add_coin')],
        [InlineKeyboardButton("📋 Мои монеты", callback_data='my_coins')],
        [InlineKeyboardButton("💰 Узнать цену", callback_data='check_price')],
        [InlineKeyboardButton("⚙️ Настройка порогов", callback_data='thresholds')],
        [InlineKeyboardButton("🔍 Проверить изменения", callback_data='check_changes')],
        [InlineKeyboardButton("❓ Помощь", callback_data='help')]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_coins_menu(user_id):
    """Меню монет пользователя"""
    coins = db.get_user_coins(user_id)
    keyboard = []
    
    # Кнопки монет (максимум 8 на экран)
    for i in range(0, len(coins), 2):
        row = []
        if i < len(coins):
            row.append(InlineKeyboardButton(f"• {coins[i]}", callback_data=f'coin_{coins[i]}'))
        if i + 1 < len(coins):
            row.append(InlineKeyboardButton(f"• {coins[i+1]}", callback_data=f'coin_{coins[i+1]}'))
        if row:
            keyboard.append(row)
    
    # Кнопки управления
    if coins:
        keyboard.append([InlineKeyboardButton("🗑 Удалить монету", callback_data='delete_coin')])
        keyboard.append([InlineKeyboardButton("📊 Обзор порогов", callback_data='view_thresholds')])
    
    keyboard.append([InlineKeyboardButton("➕ Добавить ещё", callback_data='add_coin')])
    keyboard.append([InlineKeyboardButton("🔙 В меню", callback_data='back_to_main')])
    
    return InlineKeyboardMarkup(keyboard)

def get_thresholds_menu():
    """Меню настройки порогов"""
    keyboard = [
        [InlineKeyboardButton("📊 Общий порог", callback_data='general_threshold')],
        [InlineKeyboardButton("🔸 Для конкретной монеты", callback_data='coin_threshold')],
        [InlineKeyboardButton("👁 Обзор всех порогов", callback_data='view_all_thresholds')],
        [InlineKeyboardButton("🔙 В меню", callback_data='back_to_main')]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_popular_coins_menu():
    """Меню популярных монет"""
    keyboard = [
        [
            InlineKeyboardButton("₿ Bitcoin", callback_data='add_bitcoin'),
            InlineKeyboardButton("Ξ Ethereum", callback_data='add_ethereum')
        ],
        [
            InlineKeyboardButton("◎ Solana", callback_data='add_solana'),
            InlineKeyboardButton("₳ Cardano", callback_data='add_cardano')
        ],
        [
            InlineKeyboardButton(" Polkadot", callback_data='add_polkadot'),
            InlineKeyboardButton("✕ XRP", callback_data='add_ripple')
        ],
        [
            InlineKeyboardButton("Ð Doge", callback_data='add_dogecoin'),
            InlineKeyboardButton("Ł Litecoin", callback_data='add_litecoin')
        ],
        [
            InlineKeyboardButton("🐸 Pepe", callback_data='add_pepe'),
            InlineKeyboardButton("🐕 Shiba", callback_data='add_shiba-inu')
        ],
        [InlineKeyboardButton("✏️ Ввести свою", callback_data='add_custom')],
        [InlineKeyboardButton("🔙 В меню", callback_data='back_to_main')]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_threshold_values_menu():
    """Меню выбора порога"""
    keyboard = [
        [
            InlineKeyboardButton("0.5%", callback_data='threshold_0.5'),
            InlineKeyboardButton("1%", callback_data='threshold_1'),
            InlineKeyboardButton("2%", callback_data='threshold_2')
        ],
        [
            InlineKeyboardButton("3%", callback_data='threshold_3'),
            InlineKeyboardButton("5%", callback_data='threshold_5'),
            InlineKeyboardButton("10%", callback_data='threshold_10')
        ],
        [InlineKeyboardButton("✏️ Ввести своё", callback_data='threshold_custom')],
        [InlineKeyboardButton("🔙 Назад", callback_data='thresholds')]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_coin_threshold_menu(coin_name):
    """Меню порога для конкретной монеты"""
    keyboard = [
        [
            InlineKeyboardButton("0.5%", callback_data=f'cth_{coin_name}_0.5'),
            InlineKeyboardButton("1%", callback_data=f'cth_{coin_name}_1'),
            InlineKeyboardButton("2%", callback_data=f'cth_{coin_name}_2')
        ],
        [
            InlineKeyboardButton("3%", callback_data=f'cth_{coin_name}_3'),
            InlineKeyboardButton("5%", callback_data=f'cth_{coin_name}_5'),
            InlineKeyboardButton("10%", callback_data=f'cth_{coin_name}_10')
        ],
        [InlineKeyboardButton("✏️ Ввести своё", callback_data=f'cth_custom_{coin_name}')],
        [InlineKeyboardButton("🗑 Удалить инд. порог", callback_data=f'remove_cth_{coin_name}')],
        [InlineKeyboardButton("🔙 К монете", callback_data=f'coin_{coin_name}')]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_back_menu():
    """Простое меню назад"""
    return InlineKeyboardMarkup([[InlineKeyboardButton("🔙 В меню", callback_data='back_to_main')]])

# ========== ОБРАБОТЧИКИ КОМАНД ==========

async def start(update: Update, context: CallbackContext) -> None:
    """Обработчик команды /start с кнопочным меню"""
    user = update.effective_user
    db.add_user(user.id, user.username or user.first_name)
    
    await update.message.reply_text(
        f"👋 Привет, {user.first_name}!\n"
        "🤖 Я бот для отслеживания цен на криптовалюты\n\n"
        "🎛 *Выберите действие:*",
        reply_markup=get_main_menu(),
        parse_mode='Markdown'
    )

async def help_command(update: Update, context: CallbackContext) -> None:
    """Обработчик команды /help"""
    await update.message.reply_text(
        "📚 *Помощь по кнопкам:*\n\n"
        "➕ *Добавить монету* - выбрать из популярных или ввести свою\n"
        "📋 *Мои монеты* - список ваших монет и управление ими\n"
        "💰 *Узнать цену* - быстрая проверка цены любой монеты\n"
        "⚙️ *Настройка порогов* - установка порогов уведомлений\n"
        "🔍 *Проверить изменения* - проверка изменений цен\n\n"
        "💡 *Совет:* Используйте кнопки для быстрого управления!",
        reply_markup=get_back_menu(),
        parse_mode='Markdown'
    )

async def cancel_command(update: Update, context: CallbackContext) -> None:
    """Обработчик команды /cancel"""
    user = update.effective_user
    if 'user_states' in context.chat_data:
        context.chat_data['user_states'].pop(user.id, None)
    
    await update.message.reply_text(
        "❌ Действие отменено",
        reply_markup=get_main_menu()
    )

# ========== ОБРАБОТЧИКИ КНОПОК ==========

async def button_handler(update: Update, context: CallbackContext) -> None:
    """Обработчик нажатий на кнопки"""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    data = query.data
    
    # Инициализируем состояния пользователя
    if 'user_states' not in context.chat_data:
        context.chat_data['user_states'] = {}
    
    # Главное меню
    if data == 'back_to_main':
        await show_main_menu(query)
    
    # Добавить монету
    elif data == 'add_coin':
        await show_add_coin_menu(query)
    
    # Мои монеты
    elif data == 'my_coins':
        await show_my_coins(query, user.id)
    
    # Узнать цену
    elif data == 'check_price':
        context.chat_data['user_states'][user.id] = 'awaiting_coin_price'
        await query.edit_message_text(
            "💰 *Узнать цену монеты*\n\n"
            "Введите название монеты:\n"
            "(например: bitcoin, ethereum, solana)\n\n"
            "Или нажмите /cancel для отмены",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 В меню", callback_data='back_to_main')]
            ])
        )
    
    # Настройка порогов
    elif data == 'thresholds':
        await show_thresholds_menu(query)
    
    # Проверить изменения
    elif data == 'check_changes':
        await check_price_changes(query, user.id)
    
    # Помощь
    elif data == 'help':
        await help_button(query)
    
    # Добавление любой монеты (начинается с add_)
    elif data.startswith('add_'):
        if data == 'add_custom':
            context.chat_data['user_states'][user.id] = 'awaiting_coin_name'
            await query.edit_message_text(
                "➕ *Добавить свою монету*\n\n"
                "Введите название монеты на английском:\n"
                "(например: bitcoin, ethereum, solana)\n\n"
                "Или нажмите /cancel для отмены",
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 В меню", callback_data='back_to_main')]
                ])
            )
        else:
            # Извлекаем название монеты из callback_data
            # Формат: add_bitcoin, add_ethereum, add_pepe и т.д.
            coin_name = data[4:]  # Убираем 'add_'
            await process_add_coin(query, user.id, coin_name)
    
    # Выбор монеты из списка
    elif data.startswith('coin_') and not data.startswith('coin_threshold'):
        coin_name = data[5:]  # Убираем 'coin_'
        await show_coin_details(query, user.id, coin_name)
    
    # Удалить монету
    elif data == 'delete_coin':
        context.chat_data['user_states'][user.id] = 'awaiting_coin_delete'
        await query.edit_message_text(
            "🗑 *Удалить монету*\n\n"
            "Введите название монеты для удаления:\n"
            "(или выберите из списка выше)\n\n"
            "Или нажмите /cancel для отмены",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 В меню", callback_data='back_to_main')]
            ])
        )
    
    # Подтверждение удаления монеты
    elif data.startswith('delete_') and data.endswith('_confirm'):
        coin_name = data[7:-8]  # Убираем 'delete_' и '_confirm'
        await confirm_delete_coin(query, user.id, coin_name)
    
    # Удаление монеты после подтверждения
    elif data.startswith('delete_'):
        coin_name = data[7:]  # Убираем 'delete_'
        await delete_coin_from_button(query, user.id, coin_name)
    
    # Обзор порогов
    elif data == 'view_thresholds':
        await show_user_thresholds(query, user.id)
    
    # Общий порог
    elif data == 'general_threshold':
        await show_general_threshold_menu(query, user.id)
    
    # Порог для конкретной монеты
    elif data == 'coin_threshold':
        await show_coin_threshold_selection(query, user.id)
    
    # Обзор всех порогов
    elif data == 'view_all_thresholds':
        await show_all_thresholds(query, user.id)
    
    # Выбор значения общего порога
    elif data.startswith('threshold_'):
        if data == 'threshold_custom':
            context.chat_data['user_states'][user.id] = 'awaiting_general_threshold'
            await query.edit_message_text(
                "⚙️ *Установить общий порог*\n\n"
                "Введите значение порога в %:\n"
                "(например: 1.5, 2, 0.5)\n\n"
                "Или нажмите /cancel для отмены",
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 Назад", callback_data='general_threshold')]
                ])
            )
        else:
            threshold = float(data[10:])  # Убираем 'threshold_'
            await set_general_threshold(query, user.id, threshold)
    
    # Меню порога для конкретной монеты
    elif data.startswith('cth_') and data.endswith('_menu'):
        coin_name = data[4:-5]  # Убираем 'cth_' и '_menu'
        await show_coin_threshold_menu(query, user.id, coin_name)
    
    # Ввод своего порога для монеты
    elif data.startswith('cth_custom_'):
        coin_name = data[11:]  # Убираем 'cth_custom_'
        context.chat_data['user_states'][user.id] = {'action': 'set_coin_threshold', 'coin': coin_name}
        await query.edit_message_text(
            f"✏️ *Индивидуальный порог для {coin_name.upper()}*\n\n"
            f"Введите значение порога в %:\n"
            f"(например: 1.5, 2, 0.5)\n\n"
            f"Или нажмите /cancel для отмены",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Назад", callback_data=f'cth_{coin_name}_menu')]
            ])
        )
    
    # Установка порога для монеты
    elif data.startswith('cth_'):
        # Формат: cth_bitcoin_1
        parts = data.split('_')
        if len(parts) >= 3:
            coin_name = parts[1]
            threshold = float(parts[2])
            await set_coin_threshold(query, user.id, coin_name, threshold)
    
    # Удаление индивидуального порога
    elif data.startswith('remove_cth_'):
        coin_name = data[12:]  # Убираем 'remove_cth_'
        await remove_individual_threshold(query, user.id, coin_name)
    
    # Узнать цену монеты
    elif data.startswith('price_'):
        coin_name = data[6:]  # Убираем 'price_'
        await check_single_price_from_button(query, user.id, coin_name)
    
    # Неизвестная команда
    else:
        await query.edit_message_text(
            "❌ Неизвестная команда",
            reply_markup=get_main_menu()
        )

async def show_main_menu(query):
    """Показать главное меню"""
    await query.edit_message_text(
        "🎛 *Главное меню*\n\n"
        "Выберите действие:",
        reply_markup=get_main_menu(),
        parse_mode='Markdown'
    )

async def show_add_coin_menu(query):
    """Показать меню добавления монеты"""
    await query.edit_message_text(
        "➕ *Добавить монету*\n\n"
        "Выберите популярную монету или введите свою:",
        reply_markup=get_popular_coins_menu(),
        parse_mode='Markdown'
    )

async def show_my_coins(query, user_id):
    """Показать мои монеты"""
    coins = db.get_user_coins(user_id)
    
    if not coins:
        await query.edit_message_text(
            "📭 *У вас пока нет монет*\n\n"
            "Добавьте первую монету:",
            reply_markup=get_popular_coins_menu(),
            parse_mode='Markdown'
        )
        return
    
    coins_text = "\n".join([f"• *{coin}*" for coin in coins])
    
    await query.edit_message_text(
        f"📋 *Ваши монеты:*\n{coins_text}\n\n"
        f"📊 Всего: *{len(coins)} монет*\n\n"
        "Выберите монету для управления:",
        reply_markup=get_coins_menu(user_id),
        parse_mode='Markdown'
    )

async def show_thresholds_menu(query):
    """Показать меню порогов"""
    await query.edit_message_text(
        "⚙️ *Настройка порогов уведомлений*\n\n"
        "Выберите тип настройки:",
        reply_markup=get_thresholds_menu(),
        parse_mode='Markdown'
    )

async def process_add_coin(query, user_id, coin_name):
    """Обработать добавление монеты"""
    # Проверяем существует ли монета
    if not crypto_api.check_coin_exists(coin_name):
        await query.edit_message_text(
            f"❌ *Монета не найдена*\n\n"
            f"'{coin_name}' не найдена в базе данных.\n"
            f"Проверьте правильность написания.\n\n"
            f"💡 *Совет:* Используйте английские названия в нижнем регистре",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("✏️ Попробовать снова", callback_data='add_custom')],
                [InlineKeyboardButton("🔙 В меню", callback_data='back_to_main')]
            ]),
            parse_mode='Markdown'
        )
        return
    
    # Добавляем монету
    if db.add_coin(user_id, coin_name):
        # Получаем цену
        price = crypto_api.get_price(coin_name)
        
        if price:
            # Сохраняем начальную цену
            user_id_str = str(user_id)
            db.data[user_id_str]['last_prices'][coin_name] = price
            db._save_data()
            
            price_text = f"\n💰 *Текущая цена:* ${price:,.4f}"
        else:
            price_text = ""
        
        # Показываем текущий порог
        current_threshold = db.get_coin_threshold(user_id, coin_name)
        
        await query.edit_message_text(
            f"✅ *{coin_name.upper()} добавлена!*{price_text}\n"
            f"⚖️ *Текущий порог:* {current_threshold}%\n\n"
            "Что дальше?",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⚙️ Настроить порог", callback_data=f'cth_{coin_name}_menu')],
                [InlineKeyboardButton("➕ Добавить ещё", callback_data='add_coin')],
                [InlineKeyboardButton("📋 Мои монеты", callback_data='my_coins')],
                [InlineKeyboardButton("🔙 В меню", callback_data='back_to_main')]
            ]),
            parse_mode='Markdown'
        )
    else:
        await query.edit_message_text(
            f"ℹ️ *{coin_name}* уже в вашем списке.\n"
            f"Перейти к управлению?",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📋 Управлять", callback_data=f'coin_{coin_name}')],
                [InlineKeyboardButton("➕ Добавить другую", callback_data='add_coin')],
                [InlineKeyboardButton("🔙 В меню", callback_data='back_to_main')]
            ]),
            parse_mode='Markdown'
        )

async def show_coin_details(query, user_id, coin_name):
    """Показать детали монеты"""
    # Получаем текущую цену
    price = crypto_api.get_price(coin_name)
    threshold = db.get_coin_threshold(user_id, coin_name)
    
    # Определяем тип порога
    user_id_str = str(user_id)
    threshold_type = "🔸 индивидуальный" if coin_name in db.data[user_id_str].get('coin_thresholds', {}) else "📊 общий"
    
    price_text = f"💰 *Цена:* ${price:,.4f}\n" if price else ""
    
    await query.edit_message_text(
        f"📊 *{coin_name.upper()}*\n\n"
        f"{price_text}"
        f"⚖️ *Порог:* {threshold}% ({threshold_type})\n\n"
        "Выберите действие:",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("⚙️ Изменить порог", callback_data=f'cth_{coin_name}_menu')],
            [InlineKeyboardButton("💰 Обновить цену", callback_data=f'price_{coin_name}')],
            [InlineKeyboardButton("🗑 Удалить монету", callback_data=f'delete_{coin_name}_confirm')],
            [InlineKeyboardButton("📋 К списку", callback_data='my_coins')],
            [InlineKeyboardButton("🔙 В меню", callback_data='back_to_main')]
        ]),
        parse_mode='Markdown'
    )

async def check_price_changes(query, user_id):
    """Проверить изменения цен"""
    user_id_str = str(user_id)
    if user_id_str not in db.data:
        await query.edit_message_text(
            "📭 *У вас нет монет*\n\n"
            "Сначала добавьте монеты:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("➕ Добавить монету", callback_data='add_coin')],
                [InlineKeyboardButton("🔙 В меню", callback_data='back_to_main')]
            ]),
            parse_mode='Markdown'
        )
        return
    
    coins = db.data[user_id_str].get('coins', [])
    
    if not coins:
        await query.edit_message_text(
            "📭 *У вас нет монет*\n\n"
            "Сначала добавьте монеты:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("➕ Добавить монету", callback_data='add_coin')],
                [InlineKeyboardButton("🔙 В меню", callback_data='back_to_main')]
            ]),
            parse_mode='Markdown'
        )
        return
    
    await query.edit_message_text(
        "🔍 *Проверяю изменения цен...*\n\n"
        "⏳ Пожалуйста, подождите...",
        parse_mode='Markdown'
    )
    
    changes_found = False
    changes_text = ""
    changes_count = 0
    
    for coin_name in coins:
        current_price = crypto_api.get_price(coin_name)
        if not current_price:
            continue
        
        last_price = db.data[user_id_str].get('last_prices', {}).get(coin_name)
        
        if last_price is not None:
            # Получаем порог
            threshold = db.get_coin_threshold(user_id, coin_name)
            
            price_change = abs((current_price - last_price) / last_price * 100)
            
            if price_change >= threshold:
                changes_found = True
                changes_count += 1
                direction = "📈" if current_price > last_price else "📉"
                dir_text = "РОСТ" if current_price > last_price else "ПАДЕНИЕ"
                changes_text += f"\n{direction} *{coin_name.upper()}* - {dir_text}\n"
                changes_text += f"   Изменение: *{price_change:.2f}%*\n"
                changes_text += f"   Было: ${last_price:.4f}\n"
                changes_text += f"   Стало: ${current_price:.4f}\n"
        
        # Обновляем цену
        db.update_price(user_id, coin_name, current_price)
    
    # Создаем клавиатуру для возврата
    keyboard = [
        [InlineKeyboardButton("🔍 Проверить снова", callback_data='check_changes')],
        [InlineKeyboardButton("📋 Мои монеты", callback_data='my_coins')],
        [InlineKeyboardButton("🔙 В меню", callback_data='back_to_main')]
    ]
    
    if changes_found:
        await query.edit_message_text(
            f"🔔 *Обнаружены изменения!*\n\n"
            f"Найдено изменений: *{changes_count}* из {len(coins)}\n"
            f"{changes_text}\n"
            f"✅ Проверка завершена",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    else:
        await query.edit_message_text(
            f"✅ *Изменений не обнаружено*\n\n"
            f"Цены ваших *{len(coins)} монет* не изменились на заданные пороги.\n\n"
            f"🔍 Следующая проверка - когда захотите!",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )

async def help_button(query):
    """Показать помощь"""
    await query.edit_message_text(
        "📚 *Помощь по кнопкам:*\n\n"
        "➕ *Добавить монету* - выбрать из популярных или ввести свою\n"
        "📋 *Мои монеты* - список ваших монет и управление ими\n"
        "💰 *Узнать цену* - быстрая проверка цены любой монеты\n"
        "⚙️ *Настройка порогов* - установка порогов уведомлений\n"
        "🔍 *Проверить изменения* - проверка изменений цен\n\n"
        "💡 *Совет:* Используйте кнопки для быстрого управления!",
        reply_markup=get_back_menu(),
        parse_mode='Markdown'
    )

async def show_general_threshold_menu(query, user_id):
    """Показать меню общего порога"""
    user_data = db.get_user(user_id)
    current_threshold = user_data['threshold'] if user_data else 1.0
    
    await query.edit_message_text(
        f"📊 *Общий порог уведомлений*\n\n"
        f"Текущий общий порог: *{current_threshold}%*\n\n"
        f"Этот порог применяется ко всем монетам, у которых нет индивидуального порога.\n\n"
        f"Выберите новое значение:",
        reply_markup=get_threshold_values_menu(),
        parse_mode='Markdown'
    )

async def set_general_threshold(query, user_id, threshold):
    """Установить общий порог"""
    if db.set_threshold(user_id, threshold):
        await query.edit_message_text(
            f"✅ *Общий порог установлен!*\n\n"
            f"Теперь вы будете получать уведомления при изменении цены на *{threshold}%* или более.\n\n"
            f"Этот порог применяется ко всем монетам, у которых нет индивидуального порога.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("👁 Обзор порогов", callback_data='view_all_thresholds')],
                [InlineKeyboardButton("⚙️ Ещё настройки", callback_data='thresholds')],
                [InlineKeyboardButton("🔙 В меню", callback_data='back_to_main')]
            ]),
            parse_mode='Markdown'
        )
    else:
        await query.edit_message_text(
            "❌ Ошибка при установке порога",
            reply_markup=get_back_menu()
        )

async def show_coin_threshold_selection(query, user_id):
    """Показать выбор монеты для установки порога"""
    coins = db.get_user_coins(user_id)
    
    if not coins:
        await query.edit_message_text(
            "📭 *У вас нет монет*\n\n"
            "Сначала добавьте монеты:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("➕ Добавить монету", callback_data='add_coin')],
                [InlineKeyboardButton("🔙 Назад", callback_data='thresholds')]
            ]),
            parse_mode='Markdown'
        )
        return
    
    # Создаем кнопки для каждой монеты
    keyboard = []
    for i in range(0, len(coins), 2):
        row = []
        if i < len(coins):
            row.append(InlineKeyboardButton(coins[i], callback_data=f'cth_{coins[i]}_menu'))
        if i + 1 < len(coins):
            row.append(InlineKeyboardButton(coins[i+1], callback_data=f'cth_{coins[i+1]}_menu'))
        if row:
            keyboard.append(row)
    
    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data='thresholds')])
    
    await query.edit_message_text(
        "🔸 *Порог для конкретной монеты*\n\n"
        "Выберите монету для настройки индивидуального порога:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

async def show_coin_threshold_menu(query, user_id, coin_name):
    """Показать меню порога для конкретной монеты"""
    current_threshold = db.get_coin_threshold(user_id, coin_name)
    
    await query.edit_message_text(
        f"⚙️ *Индивидуальный порог для {coin_name.upper()}*\n\n"
        f"Текущий порог: *{current_threshold}%*\n\n"
        f"Выберите новое значение:\n"
        f"(индивидуальный порог имеет приоритет над общим)",
        reply_markup=get_coin_threshold_menu(coin_name),
        parse_mode='Markdown'
    )

async def set_coin_threshold(query, user_id, coin_name, threshold):
    """Установить порог для конкретной монеты"""
    if db.set_coin_threshold(user_id, coin_name, threshold):
        await query.edit_message_text(
            f"✅ *Порог установлен!*\n\n"
            f"Для *{coin_name.upper()}* порог: *{threshold}%*\n\n"
            f"Теперь вы будете получать уведомления при изменении цены {coin_name} на {threshold}% или более.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("👁 Обзор порогов", callback_data='view_all_thresholds')],
                [InlineKeyboardButton("🔙 К монете", callback_data=f'coin_{coin_name}')],
                [InlineKeyboardButton("🔙 В меню", callback_data='back_to_main')]
            ]),
            parse_mode='Markdown'
        )
    else:
        await query.edit_message_text(
            "❌ Ошибка при установке порога",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 К монете", callback_data=f'coin_{coin_name}')],
                [InlineKeyboardButton("🔙 В меню", callback_data='back_to_main')]
            ])
        )

async def remove_individual_threshold(query, user_id, coin_name):
    """Удалить индивидуальный порог"""
    user_id_str = str(user_id)
    if user_id_str in db.data:
        coin_thresholds = db.data[user_id_str].get('coin_thresholds', {})
        if coin_name in coin_thresholds:
            del coin_thresholds[coin_name]
            db._save_data()
            
            await query.edit_message_text(
                f"✅ *Индивидуальный порог удалён*\n\n"
                f"Для *{coin_name.upper()}* теперь будет применяться общий порог.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 К монете", callback_data=f'coin_{coin_name}')],
                    [InlineKeyboardButton("🔙 В меню", callback_data='back_to_main')]
                ]),
                parse_mode='Markdown'
            )
            return
    
    await query.edit_message_text(
        "❌ Индивидуальный порог не найден",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 К монете", callback_data=f'coin_{coin_name}')],
            [InlineKeyboardButton("🔙 В меню", callback_data='back_to_main')]
        ])
    )

async def show_user_thresholds(query, user_id):
    """Показать пороги пользователя"""
    coins = db.get_user_coins(user_id)
    user_data = db.get_user(user_id)
    general_threshold = user_data['threshold'] if user_data else 1.0
    
    if not coins:
        await query.edit_message_text(
            "📭 *У вас нет монет*\n\n"
            "Сначала добавьте монеты:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("➕ Добавить монету", callback_data='add_coin')],
                [InlineKeyboardButton("🔙 В меню", callback_data='back_to_main')]
            ]),
            parse_mode='Markdown'
        )
        return
    
    thresholds_text = f"📊 *Общий порог:* {general_threshold}%\n\n"
    thresholds_text += "*Пороги по монетам:*\n"
    
    for coin in coins:
        threshold = db.get_coin_threshold(user_id, coin)
        threshold_type = "🔸 инд." if coin in user_data.get('coin_thresholds', {}) else "📊 общ."
        thresholds_text += f"• *{coin}*: {threshold}% ({threshold_type})\n"
    
    await query.edit_message_text(
        thresholds_text,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("⚙️ Настроить пороги", callback_data='thresholds')],
            [InlineKeyboardButton("📋 Мои монеты", callback_data='my_coins')],
            [InlineKeyboardButton("🔙 В меню", callback_data='back_to_main')]
        ]),
        parse_mode='Markdown'
    )

async def show_all_thresholds(query, user_id):
    """Показать все пороги"""
    await show_user_thresholds(query, user_id)

async def confirm_delete_coin(query, user_id, coin_name):
    """Подтверждение удаления монеты"""
    await query.edit_message_text(
        f"⚠️ *Подтверждение удаления*\n\n"
        f"Вы уверены, что хотите удалить монету *{coin_name.upper()}*?\n\n"
        f"Это действие нельзя отменить!",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton("✅ Да, удалить", callback_data=f'delete_{coin_name}'),
                InlineKeyboardButton("❌ Нет, отменить", callback_data=f'coin_{coin_name}')
            ]
        ]),
        parse_mode='Markdown'
    )

async def delete_coin_from_button(query, user_id, coin_name):
    """Удалить монету после подтверждения"""
    user_id_str = str(user_id)
    if user_id_str in db.data and coin_name in db.data[user_id_str]['coins']:
        # Удаляем монету
        db.data[user_id_str]['coins'].remove(coin_name)
        
        # Удаляем индивидуальный порог если есть
        if coin_name in db.data[user_id_str].get('coin_thresholds', {}):
            del db.data[user_id_str]['coin_thresholds'][coin_name]
        
        # Удаляем последнюю цену если есть
        if coin_name in db.data[user_id_str].get('last_prices', {}):
            del db.data[user_id_str]['last_prices'][coin_name]
        
        db._save_data()
        
        remaining = len(db.data[user_id_str]['coins'])
        
        await query.edit_message_text(
            f"✅ *{coin_name.upper()} удалена!*\n\n"
            f"Осталось монет: *{remaining}*\n\n"
            "Что дальше?",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📋 Мои монеты", callback_data='my_coins')],
                [InlineKeyboardButton("➕ Добавить монету", callback_data='add_coin')],
                [InlineKeyboardButton("🔙 В меню", callback_data='back_to_main')]
            ]),
            parse_mode='Markdown'
        )
    else:
        await query.edit_message_text(
            f"❌ Монета *{coin_name}* не найдена",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📋 Мои монеты", callback_data='my_coins')],
                [InlineKeyboardButton("🔙 В меню", callback_data='back_to_main')]
            ]),
            parse_mode='Markdown'
        )

async def check_single_price_from_button(query, user_id, coin_name):
    """Проверить цену одной монеты из кнопки"""
    # Проверяем существует ли монета
    if not crypto_api.check_coin_exists(coin_name):
        await query.edit_message_text(
            f"❌ Монета '{coin_name}' не найдена\n"
            f"Проверьте правильность написания.",
            reply_markup=get_back_menu()
        )
        return
    
    # Получаем цену
    price = crypto_api.get_price(coin_name)
    
    if price:
        await query.edit_message_text(
            f"💰 *{coin_name.upper()}*\n"
            f"📈 Цена: *${price:,.4f}*\n\n"
            f"🕐 {datetime.now().strftime('%H:%M:%S')}",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("➕ Добавить в отслеживание", callback_data=f'add_{coin_name}')],
                [InlineKeyboardButton("💰 Узнать другую цену", callback_data='check_price')],
                [InlineKeyboardButton("🔙 В меню", callback_data='back_to_main')]
            ]),
            parse_mode='Markdown'
        )
    else:
        await query.edit_message_text(
            f"⚠️ Не удалось получить цену *{coin_name}*\n"
            f"Попробуйте позже.",
            reply_markup=get_back_menu(),
            parse_mode='Markdown'
        )

# ========== ОБРАБОТЧИКИ ТЕКСТОВЫХ СООБЩЕНИЙ ==========

async def handle_message(update: Update, context: CallbackContext) -> None:
    """Обработчик текстовых сообщений"""
    user = update.effective_user
    message_text = update.message.text.strip().lower()
    
    if not message_text:
        return
    
    # Добавляем пользователя если его нет
    db.add_user(user.id, user.username or user.first_name)
    
    # Проверяем состояние пользователя
    user_state = context.chat_data.get('user_states', {}).get(user.id)
    
    if isinstance(user_state, dict):
        # Сложное состояние (например, для установки порога монеты)
        if user_state.get('action') == 'set_coin_threshold':
            coin_name = user_state.get('coin')
            try:
                threshold = float(message_text)
                if 0.1 <= threshold <= 50:
                    if db.set_coin_threshold(user.id, coin_name, threshold):
                        await update.message.reply_text(
                            f"✅ Для *{coin_name.upper()}* порог установлен: {threshold}%",
                            reply_markup=get_main_menu(),
                            parse_mode='Markdown'
                        )
                    else:
                        await update.message.reply_text(
                            "❌ Ошибка при установке порога",
                            reply_markup=get_main_menu()
                        )
                else:
                    await update.message.reply_text(
                        "❌ Введите число от 0.1 до 50",
                        reply_markup=get_main_menu()
                    )
            except ValueError:
                await update.message.reply_text(
                    "❌ Введите число (например: 1.5)",
                    reply_markup=get_main_menu()
                )
            context.chat_data['user_states'].pop(user.id, None)
    
    elif user_state == 'awaiting_coin_name':
        # Пользователь вводит название монеты для добавления
        await add_custom_coin(update, user.id, message_text)
        context.chat_data['user_states'].pop(user.id, None)
    
    elif user_state == 'awaiting_coin_price':
        # Пользователь вводит название монеты для проверки цены
        await check_single_price(update, message_text)
        context.chat_data['user_states'].pop(user.id, None)
    
    elif user_state == 'awaiting_general_threshold':
        # Пользователь вводит общий порог
        try:
            threshold = float(message_text)
            if 0.1 <= threshold <= 50:
                if db.set_threshold(user.id, threshold):
                    await update.message.reply_text(
                        f"✅ Общий порог установлен: {threshold}%",
                        reply_markup=get_main_menu()
                    )
                else:
                    await update.message.reply_text(
                        "❌ Ошибка при установке порога",
                        reply_markup=get_main_menu()
                    )
            else:
                await update.message.reply_text(
                    "❌ Введите число от 0.1 до 50",
                    reply_markup=get_main_menu()
                )
        except ValueError:
            await update.message.reply_text(
                "❌ Введите число (например: 1.5)",
                reply_markup=get_main_menu()
            )
        context.chat_data['user_states'].pop(user.id, None)
    
    elif user_state == 'awaiting_coin_delete':
        # Пользователь вводит название монеты для удаления
        await delete_coin(update, user.id, message_text)
        context.chat_data['user_states'].pop(user.id, None)
    
    else:
        # Стандартная обработка
        try:
            # Проверяем, является ли это числом (порог уведомлений)
            threshold = float(message_text)
            if 0.1 <= threshold <= 50:
                db.set_threshold(user.id, threshold)
                await update.message.reply_text(
                    f"✅ Общий порог установлен: {threshold}%",
                    reply_markup=get_main_menu()
                )
            else:
                await update.message.reply_text(
                    "❌ Введите число от 0.1 до 50",
                    reply_markup=get_main_menu()
                )
        except ValueError:
            # Проверяем, является ли это названием монеты
            if crypto_api.check_coin_exists(message_text):
                # Предлагаем добавить монету
                keyboard = [
                    [InlineKeyboardButton(f"➕ Добавить {message_text}", callback_data=f'add_{message_text}')],
                    [InlineKeyboardButton("💰 Узнать цену", callback_data=f'price_{message_text}')],
                    [InlineKeyboardButton("🔙 В меню", callback_data='back_to_main')]
                ]
                await update.message.reply_text(
                    f"Найдена монета: *{message_text.upper()}*\n\nЧто вы хотите сделать?",
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode='Markdown'
                )
            else:
                await update.message.reply_text(
                    "🤔 *Я не понял ваше сообщение*\n\n"
                    "Вы можете:\n"
                    "• Ввести название монеты (bitcoin)\n"
                    "• Ввести число для порога (1.5)\n"
                    "• Использовать кнопки меню\n\n"
                    "Или нажмите /start для главного меню",
                    parse_mode='Markdown',
                    reply_markup=get_main_menu()
                )

async def add_custom_coin(update, user_id, coin_name):
    """Добавить пользовательскую монету"""
    # Проверяем существует ли монета
    if not crypto_api.check_coin_exists(coin_name):
        await update.message.reply_text(
            f"❌ Монета '{coin_name}' не найдена\n"
            f"Проверьте правильность написания.\n\n"
            f"💡 Попробуйте: pepe, shiba-inu, dogwifhat",
            reply_markup=get_main_menu()
        )
        return
    
    # Добавляем монету
    if db.add_coin(user_id, coin_name):
        # Получаем цену
        price = crypto_api.get_price(coin_name)
        
        if price:
            # Сохраняем начальную цену
            user_id_str = str(user_id)
            db.data[user_id_str]['last_prices'][coin_name] = price
            db._save_data()
            
            price_text = f"\n💰 Текущая цена: ${price:,.4f}"
        else:
            price_text = ""
        
        await update.message.reply_text(
            f"✅ *{coin_name.upper()} добавлена!*{price_text}\n\n"
            f"Что дальше?",
            reply_markup=get_main_menu(),
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(
            f"ℹ️ *{coin_name}* уже в вашем списке.",
            reply_markup=get_main_menu(),
            parse_mode='Markdown'
        )

async def check_single_price(update, coin_name):
    """Проверить цену одной монеты"""
    # Проверяем существует ли монета
    if not crypto_api.check_coin_exists(coin_name):
        await update.message.reply_text(
            f"❌ Монета '{coin_name}' не найдена\n"
            f"Проверьте правильность написания.\n\n"
            f"💡 Попробуйте: pepe, shiba-inu, dogwifhat",
            reply_markup=get_main_menu()
        )
        return
    
    # Получаем цену
    price = crypto_api.get_price(coin_name)
    
    if price:
        await update.message.reply_text(
            f"💰 *{coin_name.upper()}*\n"
            f"📈 Цена: *${price:,.4f}*\n\n"
            f"🕐 {datetime.now().strftime('%H:%M:%S')}",
            reply_markup=get_main_menu(),
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(
            f"⚠️ Не удалось получить цену *{coin_name}*\n"
            f"Попробуйте позже.",
            reply_markup=get_main_menu(),
            parse_mode='Markdown'
        )

async def delete_coin(update, user_id, coin_name):
    """Удалить монету"""
    user_id_str = str(user_id)
    if user_id_str in db.data and coin_name in db.data[user_id_str]['coins']:
        # Удаляем монету
        db.data[user_id_str]['coins'].remove(coin_name)
        
        # Удаляем индивидуальный порог если есть
        if coin_name in db.data[user_id_str].get('coin_thresholds', {}):
            del db.data[user_id_str]['coin_thresholds'][coin_name]
        
        # Удаляем последнюю цену если есть
        if coin_name in db.data[user_id_str].get('last_prices', {}):
            del db.data[user_id_str]['last_prices'][coin_name]
        
        db._save_data()
        
        remaining = len(db.data[user_id_str]['coins'])
        
        await update.message.reply_text(
            f"✅ *{coin_name.upper()} удалена!*\n\n"
            f"Осталось монет: *{remaining}*\n\n"
            "Что дальше?",
            reply_markup=get_main_menu(),
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(
            f"❌ *{coin_name}* не найдена в вашем списке.",
            reply_markup=get_main_menu(),
            parse_mode='Markdown'
        )

# ========== ЗАПУСК БОТА ==========

def main() -> None:
    """Запуск бота с кнопками"""
    if not Config.TELEGRAM_TOKEN:
        logger.error("❌ ОШИБКА: TELEGRAM_TOKEN не найден!")
        return
    
    try:
        # Создаем Application
        application = Application.builder().token(Config.TELEGRAM_TOKEN).build()
        
        # Регистрируем обработчики команд
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("cancel", cancel_command))
        
        # Регистрируем обработчик кнопок
        application.add_handler(CallbackQueryHandler(button_handler))
        
        # Регистрируем обработчик текстовых сообщений
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        
        # Запускаем бота
        logger.info("🤖 Бот с кнопками запущен...")
        logger.info("📱 Откройте Telegram и найдите своего бота")
        logger.info("🎛 Теперь есть кнопка Pepe и другие мем-коины!")
        logger.info("✅ Можно добавлять любые монеты через 'Ввести свою'")
        
        application.run_polling()
        
    except Exception as e:
        logger.error(f"❌ Ошибка при запуске бота: {e}")

if __name__ == '__main__':
    main()