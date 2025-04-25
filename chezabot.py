import os
from telegram import Update, InputMediaPhoto, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, MessageHandler, CallbackQueryHandler, filters, ContextTypes, CommandHandler
from telegram.ext import Updater

BOT_TOKEN = '7798958663:AAGIOC3abdkrGdyJprk65i1k-IZ6EoWBj2o'

# Список каналов для проверки подписки
REQUIRED_CHANNELS = [
    "@channel_one",  # замените на свой канал
]

# Ответы на ключевые слова
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

# Запуск webhook
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    
    # Добавляем обработчики
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(handle_callback))

    # Устанавливаем webhook (не забудьте заменить на свой URL!)
    app.bot.set_webhook(url="https://chezabot.onrender.com/webhook")

    print("Бот запущен через webhook!")
    app.run_webhook(listen="0.0.0.0", port=int(os.environ.get("PORT", 5000)), url_path="webhook")

if __name__ == '__main__':
    main()
