from telegram import Update, InputMediaPhoto
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

# 🔐 Вставь свой токен от BotFather
BOT_TOKEN = '7798958663:AAGIOC3abdkrGdyJprk65i1k-IZ6EoWBj2o'

# 📚 Словарь ключевых слов и их ответов
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
    # Добавь сколько угодно ключей и данных сюда
}

# 📦 Обработка сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message_text = update.message.text.strip()

    if message_text in RESPONSES:
        response = RESPONSES[message_text]
        await update.message.reply_text(response['text'])

        media = [InputMediaPhoto(media=url) for url in response['photos']]
        await update.message.reply_media_group(media)

# 🚀 Запуск бота
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Бот запущен!")
    app.run_polling()

if __name__ == '__main__':
    main()
