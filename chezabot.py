import os
import logging
from fastapi import FastAPI, Request
from telegram import Update, InputMediaPhoto, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    MessageHandler,
    filters,
    CallbackQueryHandler
)

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

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
application = None

async def is_user_subscribed(user_id: int, channel: str, context: ContextTypes.DEFAULT_TYPE) -> bool:
    try:
        member = await context.bot.get_chat_member(chat_id=channel, user_id=user_id)
        return member.status in ["member", "administrator", "creator"]
    except Exception as e:
        logger.error(f"Error checking subscription: {e}")
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
    if application is None:
        logger.error("Application not initialized")
        return {"status": "error", "message": "Bot not initialized"}
    
    try:
        json_data = await request.json()
        update = Update.de_json(json_data, application.bot)
        await application.update_queue.put(update)
        return {"status": "ok"}
    except Exception as e:
        logger.error(f"Error processing update: {e}")
        return {"status": "error", "message": str(e)}

@app.get("/")
async def health_check():
    return {
        "status": "ok", 
        "bot_initialized": application is not None and application.running
    }

@app.on_event("startup")
async def startup_event():
    global application
    
    try:
        # Инициализация бота
        application = (
            ApplicationBuilder()
            .token(BOT_TOKEN)
            .build()
        )
        
        # Регистрация обработчиков
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        application.add_handler(CallbackQueryHandler(handle_callback))
        
        # Инициализация приложения
        await application.initialize()
        
        # Установка вебхука
        webhook_url = f"https://chezabot.onrender.com/webhook/{BOT_TOKEN}"
        await application.bot.set_webhook(
            url=webhook_url,
            drop_pending_updates=True
        )
        
        # Запуск обработки обновлений
        await application.start()
        
        logger.info(f"Bot started with webhook: {webhook_url}")
        
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    if application:
        await application.stop()
        await application.shutdown()
        logger.info("Bot stopped gracefully")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
