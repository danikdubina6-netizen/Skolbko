import os
import datetime
from telethon import TelegramClient, events
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
    await event.respond(
        "👋 **Привет!** Перешли мне сообщение из любого канала/чата или от пользователя/бота, "
        "либо отправь `@username` / `ID`, и я покажу, сколько времени объект существует!"
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
        
        # Получаем дату создания (для каналов/супергрупп она есть в date)
        creation_date = getattr(entity, 'date', None)

        if not creation_date:
            # Примерный алгоритм определения даты по ID пользователя/бота
            creation_date = estimate_creation_date_by_id(entity.id)

        # Вычисляем сколько существует
        time_alive = get_age_string(creation_date)
        date_str = creation_date.strftime("%d.%m.%Y в %H:%M UTC")

        obj_type = "Канал/Группа" if getattr(entity, 'broadcast', False) or getattr(entity, 'megagroup', False) else ("Бот" if getattr(entity, 'bot', False) else "Пользователь")

        text = (
            f"📊 **Информация об объекте:**\n\n"
            f"👤 **Тип:** {obj_type}\n"
            f"🏷 **Имя/Название:** {entity.title if hasattr(entity, 'title') else entity.first_name}\n"
            f"🆔 **ID:** `{entity.id}`\n\n"
            f"📅 **Дата создания:** {date_str}\n"
            f"⏳ **Существует:** **{time_alive}**"
        )
        await event.respond(text)

    except Exception as e:
        await event.respond(f"❌ Ошибка: Не удалось найти объект или неверный юзернейм/ID.\n`{e}`")

def estimate_creation_date_by_id(user_id: int):
    """
    Примерная базовая аппроксимация ID -> Дата.
    """
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

print("Бот запущен и ожидает сообщения...")
bot.run_until_disconnected()
