import os
import datetime
from telethon import TelegramClient, events, Button
from dateutil.relativedelta import relativedelta

API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH")
BOT_TOKEN = os.environ.get("BOT_TOKEN")

bot = TelegramClient('age_checker_bot', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

def get_age_string(creation_date):
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
    # Постоянные кнопки снизу (ReplyKeyboard)
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

    # Обработка нажатий на нижние кнопки (чтобы не было ошибок поиска)
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
        await event.respond("🤖 **Проверка бота:**\nОтправь мне `@username` бота (например, `@durov`) или его `ID`.")
        return
    elif text_msg == "🆔 Мой ID":
        # Автоматически берем данные того, кто нажал кнопку
        sender = await event.get_sender()
        creation_date = estimate_creation_date_by_id(sender.id)
        time_alive = get_age_string(creation_date)
        date_str = creation_date.strftime("%d.%m.%Y в %H:%M UTC")
        
        response_text = (
            f"📊 **Твой аккаунт:**\n\n"
            f"📌 **Тип:** Пользователь\n"
            f"🏷 **Имя:** {getattr(sender, 'first_name', 'Не указано')}\n"
            f"🆔 **ID:** `{sender.id}`\n\n"
            f"📅 **Дата создания:** приблизительно {date_str}\n"
            f"⏳ **Существует:** **{time_alive}**"
        )
        await event.respond(response_text)
        return

    # Обычный поиск по введенному юзернейму, ID или репосту
    target = text_msg
    
    if event.fwd_from:
        if event.fwd_from.from_id:
            target = event.fwd_from.from_id
        elif event.fwd_from.from_name:
            await event.respond("⚠️ Не удалось получить ID из пересланного сообщения (скрытый аккаунт).")
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
        await event.respond(f"❌ Ошибка: Не удалось найти объект или неверный юзернейм/ID.\n`{e}`")

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

print("Бот запущен и ожидает сообщения...")
bot.run_until_disconnected()
        
