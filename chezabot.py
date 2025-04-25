import os
from flask import Flask, request
from telegram import Update, InputMediaPhoto, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, MessageHandler, CallbackQueryHandler, filters, ContextTypes, CommandHandler
from telegram.ext import Updater

BOT_TOKEN = '7798958663:AAGIOC3abdkrGdyJprk65i1k-IZ6EoWBj2o'


# Создание Flask-приложения
app = Flask(__name__)

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
            'https://cdn.tylat.cc/storage/screens/0/329/seryabkina-olga-golaya-108.webp',
            'https://cdn.tylat.cc/storage/screens/0/329/seryabkina-olga-golaya-109.webp',
            'https://cdn.tylat.cc/storage/screens/0/329/seryabkina-olga-golaya-110.webp',
        ]
    },
    '112': {
        'text': 'ГОЛЫЕ ФОТО АНДЖЕЛИНЫ ДЖОЛИ🔥',
        'photos': [
            'https://example.com/photo3.jpg',
            'https://example.com/photo4.jpg',
        ]
    },
}

# Проверка подписки
async def is_user_subscribed(user_id: int, channel: str, context: ContextTypes.DEFAULT_TYPE) -> bool:
    try:
        member = await context.bot.get_chat_member(chat_id=channel, user_id=user_id)
        return member.status in ["member", "administrator", "creator"]
    except:
        return False

# Отправка контента
async def send_response(update: Update, context: ContextTypes.DEFAULT_TYPE, key: str):
    response = RESPONSES[key]
    chat_id = update.effective_chat.id

    await context.bot.send_message(chat_id=chat_id, text=response['text'])
    media = [InputMediaPhoto(media=url) for url in response['photos']]
    await context.bot.send_media_group(chat_id=chat_id, media=media)

# Обработка команды /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Привет! Я бот, который присылает эксклюзивный контент по ключевым словам.\n\n"
        "📥 Просто отправь одно из ключевых слов, например:\n\n"
        "• 111\n"
        "• 112\n"
        "• ...и получи секретные материалы 👀"
    )

# Обработка сообщения
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message_text = update.message.text.strip()
    user_id = update.effective_user.id

    if message_text in RESPONSES:
        # Проверка всех каналов
        not_subscribed_channels = []
        for channel in REQUIRED_CHANNELS:
            if not await is_user_subscribed(user_id, channel, context):
                not_subscribed_channels.append(channel)

        if not_subscribed_channels:
            # Создаём кнопки
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

        # Если подписан — отправляем контент
        await send_response(update, context, message_text)

    else:
        await update.message.reply_text("Ключ не распознан. Попробуй другое слово.")

# Обработка кнопки "Проверить подписку"
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

# Flask webhook для обработки запросов Telegram
@app.route('/webhook', methods=['POST'])
def webhook():
    json_str = request.get_data(as_text=True)
    update = Update.de_json(json_str, app.bot)
    app.bot.dispatcher.process_update(update)
    return 'ok'

# Запуск webhook
def main():
    app.bot = ApplicationBuilder().token(BOT_TOKEN).build()
    
    # Добавляем обработчики
    app.bot.add_handler(CommandHandler("start", start))
    app.bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.bot.add_handler(CallbackQueryHandler(handle_callback))

 app.run_webhook(listen="0.0.0.0", port=int(os.environ.get("PORT", 5000)), url_path="webhook", webhook_url="https://chezabot.onrender.com/webhook")

if __name__ == '__main__':
    main()
