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
    # Кнопки со встроенным выбором через инлайн-режим (открывают меню выбора чатов/ботов)
    buttons = [
        [Button.inline("💬 Выбрать чат / группу", b("mode_chat"))],
        [Button.inline("📢 Выбрать канал", b("mode_channel"))],
        [Button.inline("👤 Выбрать пользователя / бота", b("mode_user"))],
        [Button.inline("🆔 Мой ID", b("btn_myid"))]
    ]
    await event.respond(
        "👋 **Привет!** Я помогу узнать возраст любого объекта.\n\n"
        "Нажми на кнопку ниже, чтобы выбрать объект из списка, или просто перешли сообщение:",
        buttons=buttons
    )

@bot.on(events.CallbackQuery)
async def callback_handler(event):
    data = event.data.decode('utf-8')
    
    if data == "mode_chat":
        await event.answer()
        await event.respond(
            "💬 Чтобы проверить чат или группу, перешли оттуда сообщение сюда или отправь `@username` / `ID`."
        )
    elif data == "mode_channel":
        await event.answer()
        await event.respond(
            "📢 Чтобы проверить канал, перешли оттуда сообщение сюда или отправь `@username` / `ID`."
        )
    elif data == "mode_user":
        await event.answer()
        await event.respond(
            "👤 Чтобы проверить пользователя или бота, перешли его сообщение сюда или отправь `@username` / `ID`."
        )
    elif data == "btn_myid":
        sender = await event.get_sender()
        await event.answer(f"Твой ID: {sender.id}", alert=True)

@bot.on(events.NewMessage)
async def check_age(event):
    if event.text.startswith('/'):
        return

    target = event.text.strip()
    
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

def b(text):
    return text.encode('utf-8')

print("Бот запущен и ожидает сообщения...")
bot.run_until_disconnected()
