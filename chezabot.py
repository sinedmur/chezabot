import os
import asyncio
from fastapi import FastAPI, Request
from telegram import Update, InputMediaPhoto, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters, CallbackQueryHandler

BOT_TOKEN = '7798958663:AAGIOC3abdkrGdyJprk65i1k-IZ6EoWBj2o'
REQUIRED_CHANNELS = [
    "@chezanovo",
    "@cheza18",
    "@chezamusics",
    "@chezaeconomic"
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

app = FastAPI()
application = ApplicationBuilder().token(BOT_TOKEN).build()

async def is_user_subscribed(user_id: int, channel: str, context: ContextTypes.DEFAULT_TYPE) -> bool:
    try:
        member = await context.bot.get_chat_member(chat_id=channel, user_id=user_id)
        return member.status in ["member", "administrator", "creator"]
    except:
        return False

async def send_response(update: Update, context: ContextTypes.DEFAULT_TYPE, key: str):
    response = RESPONSES[key]
    chat_id = update.effective_chat.id

    await context.bot.send_message(chat_id=chat_id, text=response['text'])
    media = [InputMediaPhoto(media=url) for url in response['photos']]
    await context.bot.send_media_group(chat_id=chat_id, media=media)

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

@app.post(f'/{BOT_TOKEN}')
async def webhook(request: Request):
    json_str = await request.json()
    update = Update.de_json(json_str, application.bot)
    await application.update_queue.put(update)
    return {"status": "ok"}

@app.get("/", status_code=200)
@app.head("/")
async def root():
    return {"message": "Your service is live!"}

async def set_webhook():
    webhook_url = f'https://chezabot.onrender.com/{BOT_TOKEN}'
    await application.bot.set_webhook(url=webhook_url)
    print(f"Webhook set to: {webhook_url}")

def main():
    # Добавляем обработчики
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(CallbackQueryHandler(handle_callback))

    # Для production используем webhook
    application.run_webhook(
        listen="0.0.0.0",
        port=int(os.environ.get("PORT", 10000)),
        webhook_url=f'https://chezabot.onrender.com/{BOT_TOKEN}'
    )

if __name__ == '__main__':
    main()
