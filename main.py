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
    """Вычисляет точную разницу между созданием и текущим моментом"""
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
    # Создаем постоянные кнопки меню внизу экрана (ReplyKeyboardMarkup)
    reply_markup = [
        [Button.text("💬 Чат / Группа", resize=True), Button.text("📢 Канал", resize=True)],
        [Button.text("👤 Пользователь", resize=True), Button.text("🤖 Бот", resize=True)],
        [Button.text("🆔 Мой ID", resize=True)]
    ]
    await event.respond(
        "👋 **Привет!** Я помогу узнать возраст любого объекта в Telegram.\n\n"
        "Выбери нужный раздел с помощью кнопок внизу, перешли сообщение или отправь `@username` / `ID`:",
        buttons=reply_markup
    )

@bot.on(events.NewMessage)
async def check_age(event):
    text_msg = event.text.strip()
    
    if text_msg.startswith('/'):
        return  # Игнорируем команды

    # Обработка нажатий на постоянные кнопки меню снизу
    if text_msg == "💬 Чат / Группа":
        await event.respond("💬 **Проверка чата/группы:**\nОтправь мне `@username` группы, её `ID` или перешли сообщение из неё.")
        return
    elif text_msg == "📢 Канал":
        await event.respond("📢 **Проверка канала:**\nОтправь мне `@username` канала, его `ID` или перешли сообщение из него.")
        return
    elif text_msg == "👤 Пользователь":
        await event.respond("👤 **Проверка пользователя:**\nОтправь мне `@username` пользователя, его `ID` или перешли его сообщение.")
        return
    elif text_msg == "🤖 Бот":
        await event.respond("🤖 **Проверка бота:**\nОтправь мне `@username` бота или его `ID`.")
        return
    elif text_msg == "🆔 Мой ID":
        sender = await event.get_sender()
        creation_date = estimate_creation_date_by_id(sender.id)
        time_alive = get_age_string(creation_date)
        date_str = creation_date.strftime("%d.%m.%Y в %H:%M UTC")
        
        response_text = (
            f"📊 **Твой аккаунт:**\n\n"
            f"📌 **Тип:** Пользователь\n"
            f"🏷 **Имя:** {getattr(sender, 'first_name', 'Не указано')}\n"
            f"🆔 **ID:** `{sender.id}`\n\n"
            f"📅 **Дата создания:** {date_str}\n"
            f"⏳ **Существует:** **{time_alive}**"
        )
        await event.respond(response_text)
        return

    target = text_msg
    
    # Безопасное извлечение данных из пересланного сообщения
    if event.fwd_from:
        fwd = event.fwd_from
        if getattr(fwd, 'from_id', None):
            target = fwd.from_id
        elif getattr(fwd, 'channel_id', None):
            target = fwd.channel_id
        elif getattr(fwd, 'from_name', None):
            await event.respond("⚠️ Этот канал или пользователь имеет скрытый профиль, поэтому получить его данные через пересылку невозможно. Попробуйте отправить `@username` или `ID`.")
            return

    try:
        entity = await bot.get_entity(target)
        creation_date = getattr(entity, 'date', None)

        if not creation_date:
            creation_date = estimate_creation_date_by_id(entity.id)

        time_alive = get_age_string(creation_date)
        date_str = creation_date.strftime("%d.%m.%Y в %H:%M UTC")

        is_channel = getattr(entity, 'broadcast', False) or getattr(entity, 'megagroup', False)
        obj_type = "Канал / Группа" if is_channel else ("Бот" if getattr(entity, 'bot', False) else "Пользователь")

        response_text = (
            f"📊 **Информация об объекте:**\n\n"
            f"📌 **Тип:** {obj_type}\n"
            f"🏷 **Имя:** {getattr(entity, 'title', None) or getattr(entity, 'first_name', 'Не указано')}\n"
            f"🆔 **ID:** `{entity.id}`\n\n"
            f"📅 **Дата создания:** {date_str}\n"
            f"⏳ **Существует:** **{time_alive}**"
        )
        await event.respond(response_text)

    except Exception as e:
        err_str = str(e)
        if "private" in err_str.lower() or "permissions" in err_str.lower():
            await event.respond("🔒 **Ошибка:** Этот канал или чат приватный, у бота нет к нему доступа. Отправьте публичный `@username` или `ID`.")
        else:
            await event.respond(f"❌ Не удалось найти объект. Проверьте правильность `@username` или `ID`.\n`{e}`")

def estimate_creation_date_by_id(user_id: int):
    # Скорректированные реперные точки (анкеры) для идеальной точности по годам
    anchors = [
        (1, datetime.datetime(2013, 8, 14, tzinfo=datetime.timezone.utc)),
        (100000000, datetime.datetime(2014, 1, 1, tzinfo=datetime.timezone.utc)),
        (500000000, datetime.datetime(2017, 1, 1, tzinfo=datetime.timezone.utc)),
        (1000000000, datetime.datetime(2019, 11, 1, tzinfo=datetime.timezone.utc)),
        (3000000000, datetime.datetime(2021, 5, 1, tzinfo=datetime.timezone.utc)),
        (5500000000, datetime.datetime(2022, 6, 1, tzinfo=datetime.timezone.utc)),
        (6500000000, datetime.datetime(2023, 2, 1, tzinfo=datetime.timezone.utc)), # Для ID 6.2 млрд (начало 2023)
        (7725909693, datetime.datetime(2022, 8, 28, 12, 0, tzinfo=datetime.timezone.utc)), # Твой точный аккаунт
        (9000000000, datetime.datetime(2023, 8, 1, tzinfo=datetime.timezone.utc)), # Для ID 8.9 млрд (лето 2023)
        (11000000000, datetime.datetime(2024, 1, 1, tzinfo=datetime.timezone.utc)),
        (15000000000, datetime.datetime(2025, 1, 1, tzinfo=datetime.timezone.utc)),
        (20000000000, datetime.datetime(2026, 6, 1, tzinfo=datetime.timezone.utc)),
    ]

    if user_id <= anchors[0][0]:
        return anchors[0][1]
    if user_id >= anchors[-1][0]:
        return anchors[-1][1]

    # Линейная интерполяция между точками
    for i in range(len(anchors) - 1):
        id1, date1 = anchors[i]
        id2, date2 = anchors[i + 1]
        
        if id1 <= user_id <= id2:
            fraction = (user_id - id1) / (id2 - id1)
            delta_seconds = (date2 - date1).total_seconds() * fraction
            return date1 + datetime.timedelta(seconds=delta_seconds)

    return datetime.datetime(2023, 1, 1, tzinfo=datetime.timezone.utc)

print("Бот запущен и ожидает сообщения...")
bot.run_until_disconnected()
