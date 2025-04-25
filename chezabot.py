from telegram import Update, InputMediaPhoto, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from fastapi import FastAPI, Request
import os

BOT_TOKEN = '7798958663:AAGIOC3abdkrGdyJprk65i1k-IZ6EoWBj2o'
REQUIRED_CHANNELS = [
    "@chezanovo",  # пример: @tyrneo_music
    "@cheza18",
    "@chezamusics",
    "@chezaeconomic"   # если второй есть, иначе оставь один
]

RESPONSES = {
    '111': {
        'text': 'ГОЛЫЕ ФОТО ОЛЬГИ СЕРЯБКИНОЙ📸',
        'photos': [
            'https://cdn.tylat.cc/storage/screens/0/329/seryabkina-olga-golaya-106.webp',
            'https://cdn.tylat.cc/storage/screens/0/329/seryabkina-olga-golaya-107.webp',
        ]
    },
    '112': {
        'text': 'Это ответ на 112 🔥',
        'photos': [
            'https://example.com/photo3.jpg',
            'https://example.com/photo4.jpg',
        ]
    },
}

# Создаем FastAPI приложение
app = FastAPI()

# Обработчик для корневого маршрута
@app.get("/")
async def read_root():
    return {"message": "Bot is running!"}

# ⛔️ Проверка подписки
async def is_user_subscribed(user_id: int, channel: str, context: ContextTypes.DEFAULT_TYPE) -> bool:
    try:
        member = await context.bot.get_chat_member(chat_id=channel, user_id=user_id)
        return member.status in ["member", "administrator", "creator"]
    except:
        return False

# 📤 Отправка контента
async def send_response(update: Update, context: ContextTypes.DEFAULT_TYPE, key: str):
    response = RESPONSES[key]
    chat_id = update.effective_chat.id

    await context.bot.send_message(chat_id=chat_id, text=response['text'])
    media = [InputMediaPhoto(media=url) for url in response['photos']]
    await context.bot.send_media_group(chat_id=chat_id, media=media)

# 📩 Обработка сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message_text = update.message.text.strip()
    user_id = update.effective_user.id

    if message_text in RESPONSES:
        not_subscribed_channels = []
        for channel in REQUIRED_CHANNELS:
            if not await is_user_subscribed(user_id, channel, context):
                not_subscribed_channels.append(channel)

        if not_subscribed_channels:
            buttons = [
                [InlineKeyboardButton("📢 Перейти в канал", url=f"https://t.me/{channel[1:]}")]
                for channel in not_subscribed_channels
            ]
            buttons.append([InlineKeyboardButton("✅ Проверить подписку", callback_data=f"checksub|{message_text}")])
            keyboard = InlineKeyboardMarkup(buttons)

            await update.message.reply_text(
                "Пожалуйста, подпишись на все каналы и нажми кнопку ниже:",
                reply_markup=keyboard
            )
            return

        await send_response(update, context, message_text)
    else:
        await update.message.reply_text("Ключ не распознан. Попробуй другое слово.")

# 🔘 Обработка кнопки "Проверить подписку"
async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    data = query.data

    if data.startswith("checksub"):
        _, key = data.split("|")

        not_subscribed_channels = []
        for channel in REQUIRED_CHANNELS:
            if not await is_user_subscribed(user_id, channel, context):
                not_subscribed_channels.append(channel)

        if not_subscribed_channels:
            await query.edit_message_text(
                f"❌ Подписка не найдена на: {', '.join(not_subscribed_channels)}.\nПроверь, что подписался и нажми кнопку снова."
            )
            return

        await query.edit_message_text("✅ Подписка подтверждена!")
        await send_response(update, context, key)

# 🚀 Запуск
@app.post(f'/{BOT_TOKEN}')
async def webhook(request: Request):
    json_str = await request.json()
    update = Update.de_json(json_str, application.bot)
    await application.update_queue.put(update)  # Исправлено предупреждение с await
    return {"status": "ok"}

def main():
    global application
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    # Настройка webhook с использованием await
    application.bot.set_webhook(url=f'https://chezabot.onrender.com/{BOT_TOKEN}')

    # Запуск FastAPI сервера на Render
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))

if __name__ == '__main__':
    main()
