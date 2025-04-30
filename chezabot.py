import os
import logging
import asyncio
from fastapi import FastAPI, Request
from telegram import Update, InputMediaPhoto, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    MessageHandler,
    CommandHandler,
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
    '101': {
        'text': 'ТО САМОЕ ФОТО УСПЕНСКОЙ🔥',
        'photos': [
            'https://ibb.co/1GBFBD17',
        ]
    },
    '100': {
        'text': 'ПЕРВЫЙ ТРЕЙЛЕР НОВОГО ФИЛЬМА ПРОСТОКВАШИНО🎥',
        'video': 'https://files.catbox.moe/nxuw6q.mp4'
    },
}

app = FastAPI()
application = None
keep_alive_task = None  # Для задачи поддержания активности

async def keep_alive():
    """Периодически отправляет запросы к серверу, чтобы предотвратить отключение"""
    while True:
        try:
            # Отправляем GET запрос к корневому эндпоинту
            logger.info("Sending keep-alive request")
            # Здесь можно добавить реальный HTTP запрос, если нужно
            await asyncio.sleep(300)  # Каждые 5 минут
        except Exception as e:
            logger.error(f"Keep-alive error: {e}")
            await asyncio.sleep(60)

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
    
    if 'photos' in response:
        media = [InputMediaPhoto(media=url) for url in response['photos']]
        await context.bot.send_media_group(chat_id=chat_id, media=media)
    
    if 'video' in response:
        await context.bot.send_video(chat_id=chat_id, video=response['video'])

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

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Привет! Я бот канала ЧЕ ЗА. Введи код, чтобы получить контент!\n"
        "Не забудь подписаться на все наши каналы для доступа к материалам."
    )

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
        "bot_initialized": application is not None and application.running,
        "keep_alive_running": keep_alive_task is not None and not keep_alive_task.done()
    }

@app.on_event("startup")
async def startup_event():
    global application, keep_alive_task
    
    try:
        application = (
            ApplicationBuilder()
            .token(BOT_TOKEN)
            .build()
        )
        
        application.add_handler(CommandHandler("start", start_command))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        application.add_handler(CallbackQueryHandler(handle_callback))
        
        await application.initialize()
        
        webhook_url = f"https://chezabot.onrender.com/webhook/{BOT_TOKEN}"
        await application.bot.set_webhook(
            url=webhook_url,
            drop_pending_updates=True
        )
        
        await application.start()
        
        # Запускаем задачу поддержания активности
        keep_alive_task = asyncio.create_task(keep_alive())
        
        logger.info(f"Bot started with webhook: {webhook_url}")
        
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    global keep_alive_task
    
    if keep_alive_task:
        keep_alive_task.cancel()
        try:
            await keep_alive_task
        except asyncio.CancelledError:
            pass
            
    if application:
        await application.stop()
        await application.shutdown()
        logger.info("Bot stopped gracefully")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 10000)),
        timeout_keep_alive=300  # Увеличиваем время поддержания соединения
    )
