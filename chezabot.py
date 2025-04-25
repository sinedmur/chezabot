import os
import asyncio
from fastapi import FastAPI, Request
from telegram import Update, InputMediaPhoto, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters, CallbackQueryHandler

BOT_TOKEN = '7798958663:AAGIOC3abdkrGdyJprk65i1k-IZ6EoWBj2o'
REQUIRED_CHANNELS = ["@chezanovo", "@cheza18", "@chezamusics", "@chezaeconomic"]

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
bot_application = None  # Будет инициализирован в startup

async def is_user_subscribed(user_id: int, channel: str, context: ContextTypes.DEFAULT_TYPE) -> bool:
    try:
        member = await context.bot.get_chat_member(chat_id=channel, user_id=user_id)
        return member.status in ["member", "administrator", "creator"]
    except Exception as e:
        print(f"Error checking subscription: {e}")
        return False

async def send_response(update: Update, context: ContextTypes.DEFAULT_TYPE, key: str):
    response = RESPONSES.get(key)
    if not response:
        return
        
    chat_id = update.effective_chat.id
    await context.bot.send_message(chat_id=chat_id, text=response['text'])
    media = [InputMediaPhoto(media=url) for url in response['photos']]
    await context.bot.send_media_group(chat_id=chat_id, media=media)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message_text = update.message.text.strip()
    if message_text in RESPONSES:
        not_subscribed = []
        for channel in REQUIRED_CHANNELS:
            if not await is_user_subscribed(update.effective_user.id, channel, context):
                not_subscribed.append(channel)
        
        if not_subscribed:
            buttons = [[InlineKeyboardButton(f"📢 {ch}", url=f"https://t.me/{ch[1:]}")] 
                      for ch in not_subscribed]
            buttons.append([InlineKeyboardButton("✅ Проверить подписку", 
                          callback_data=f"checksub|{message_text}")])
            await update.message.reply_text(
                "Пожалуйста, подпишись на все каналы:",
                reply_markup=InlineKeyboardMarkup(buttons)
            )
            return
        await send_response(update, context, message_text)
    else:
        await update.message.reply_text("Ключ не распознан. Попробуйте другой.")

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data.startswith("checksub"):
        _, key = query.data.split("|")
        not_subscribed = []
        for channel in REQUIRED_CHANNELS:
            if not await is_user_subscribed(query.from_user.id, channel, context):
                not_subscribed.append(channel)
        
        if not_subscribed:
            await query.edit_message_text(
                f"❌ Вы не подписаны на: {', '.join(not_subscribed)}\nПодпишитесь и нажмите снова."
            )
            return
            
        await query.edit_message_text("✅ Подписка подтверждена!")
        await send_response(update, context, key)

@app.post(f"/webhook/{BOT_TOKEN}")
async def telegram_webhook(request: Request):
    if bot_application is None:
        return {"status": "error", "message": "Bot not initialized"}
    
    json_data = await request.json()
    update = Update.de_json(json_data, bot_application.bot)
    await bot_application.process_update(update)
    return {"status": "ok"}

@app.get("/")
async def health_check():
    return {"status": "ok", "bot_initialized": bot_application is not None}

@app.on_event("startup")
async def startup_event():
    global bot_application
    
    try:
        # Инициализация бота
        bot_application = (
            ApplicationBuilder()
            .token(BOT_TOKEN)
            .build()
        )
        
        # Регистрация обработчиков
        bot_application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        bot_application.add_handler(CallbackQueryHandler(handle_callback))
        
        # Установка вебхука
        webhook_url = f"https://chezabot.onrender.com/webhook/{BOT_TOKEN}"
        await bot_application.bot.set_webhook(
            url=webhook_url,
            drop_pending_updates=True
        )
        print(f"Webhook установлен на {webhook_url}")
        
    except Exception as e:
        print(f"Ошибка при запуске бота: {e}")
        raise

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
