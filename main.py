import os
import datetime
from telethon import TelegramClient, events, Button
from dateutil.relativedelta import relativedelta

# Читаем ключи из переменных окружения (GitHub Secrets)
API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH")
BOT_TOKEN = os.environ.get("BOT_TOKEN")

# Инициализируем бота
bot = TelegramClient('age_checker_bot', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

def get_age_string(creation_date):
    """Вычисляет разницу между созданием и текущим моментом"""
    now = datetime.datetime.now(datetime.timezone.utc)
    delta = relativedelta(now, creation_date)
    
    parts = []
    if delta.years > 0:
        parts.append(f"{delta.years} год(а/лет)")
    if delta.months > 0:
        parts.append(f"{delta.months} мес.")
    if delta.days > 0:
        parts.append(f"{delta.days} дн.")
    
    return ", ".join(parts) if parts else "Меньше дня"

@bot.on(events.NewMessage(pattern='/start'))
async def start_handler(event):
    # Приветствие с кнопками выбора
    buttons = [
        [Button.inline("🔍 Проверить канал / чат", b("check_channel"))],
        [Button.inline("👤 Проверить пользователя / бота", b("check_user"))],
        [Button.inline("ℹ️ Как это работает?", b("help_info"))]
    ]
    await event.respond(
        "👋 **Привет!** Я бот для определения возраста любых объектов в Telegram.\n\n"
        "Выбери действие с помощью кнопок ниже или просто перешли мне сообщение/скинь `@username` / `ID`:",
        buttons=buttons
    )

@bot.on(events.CallbackQuery)
async def callback_handler(event):
    data = event.data.decode('utf-8')
    
    if data == "check_channel":
        await event.edit(
            "📢 **Проверка канала или группы:**\n\n"
            "Перешли мне любое сообщение из нужного канала/чата ИЛИ отправь его `@username` / `ID`.",
            buttons=[[Button.inline("« Назад", b("back_to_start"))]]
        )
    elif data == "check_user":
        await event.edit(
            "👤 **Проверка пользователя или бота:**\n\n"
            "Перешли мне сообщение от этого пользователя/бота ИЛИ отправь его `@username` / `ID`.",
            buttons=[[Button.inline("« Назад", b("back_to_start"))]]
        )
    elif data == "help_info":
        await event.edit(
            "ℹ️ **Справка:**\n\n"
            "• Для каналов и супергрупп бот находит точную дату создания.\n"
            "• Для пользователей и ботов возраст оценивается по уникальному ID Telegram.\n\n"
            "Просто отправь мне данные в чат!",
            buttons=[[Button.inline("« Назад", b("back_to_start"))]]
        )
    elif data == "back_to_start":
        buttons = [
            [Button.inline("🔍 Проверить канал / чат", b("check_channel"))],
            [Button.inline("👤 Проверить пользователя / бота", b("check_user"))],
            [Button.inline("ℹ️ Как это работает?", b("help_info"))]
        ]
        await event.edit(
            "👋 **Главное меню:** Выбери нужный пункт или отправь `@username` / `ID` / перешли сообщение:",
            buttons=buttons
        )

@bot.on(events.NewMessage)
async def check_age(event):
    if event.text.startswith('/'):
        return  # Игнорируем команды

    target = event.text.strip()
    
    # Если переслано сообщение — берём автора/чат из пересылки
    if event.fwd_from:
        if event.fwd_from.from_id:
            target = event.fwd_from.from_id
        elif event.fwd_from.from_name:
            await event.respond("⚠️ Не удалось получить ID из пересланного сообщения (скрытый аккаунт).")
            return

    try:
        entity = await bot.get_entity(target)
        
        # Получаем дату создания
        creation_date = getattr(entity, 'date', None)

        if not creation_date:
            creation_date = estimate_creation_date_by_id(entity.id)

        time_alive = get_age_string(creation_date)
        date_str = creation_date.strftime("%d.%m.%Y в %H:%M UTC")

        is_channel = getattr(entity, 'broadcast', False) or getattr(entity, 'megagroup', False)
        obj_type = "Канал / Группа" if is_channel else ("Бот" if getattr(entity, 'bot', False) else "Пользователь")

        text = (
            f"📊 **Информация об объекте:**\n\n"
            f"📌 **Тип:** {obj_type}\n"
            f"🏷 **Имя:** {getattr(entity, 'title', None) or getattr(entity, 'first_name', 'Не указано')}\n"
            f"🆔 **ID:** `{entity.id}`\n\n"
            f"📅 **Дата создания:** {date_str}\n"
            f"⏳ **Существует:** **{time_alive}**"
        )
        
        back_button = [[Button.inline("🔄 Проверить ещё", b("back_to_start"))]]
        await event.respond(text, buttons=back_button)

    except Exception as e:
        await event.respond(
            f"❌ Ошибка: Не удалось найти объект или неверный юзернейм/ID.\n`{e}`",
            buttons=[[Button.inline("« В меню", b("back_to_start"))]]
        )

def estimate_creation_date_by_id(user_id: int):
    if user_id < 100000000:
        return datetime.datetime(2014, 1, 1, tzinfo=datetime.timezone.utc)
    elif user_id < 500000000:
        return datetime.datetime(2017, 6, 1, tzinfo=datetime.timezone.utc)
    elif user_id < 1000000000:
        return datetime.datetime(2019, 12, 1, tzinfo=datetime.timezone.utc)
    elif user_id < 2000000000:
        return datetime.datetime(2021, 11, 1, tzinfo=datetime.timezone.utc)
    else:
        return datetime.datetime(2023, 5, 1, tzinfo=datetime.timezone.utc)

def b(text):
    return text.encode('utf-8')

print("Бот запущен и ожидает сообщения...")
bot.run_until_disconnected()
