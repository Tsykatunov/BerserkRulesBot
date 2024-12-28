from telegram import InlineQueryResultArticle, InputTextMessageContent, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, InlineQueryHandler, CommandHandler, CallbackQueryHandler
from glossary import glossary
import logging

logging.basicConfig(level=logging.INFO)

async def start(update, context):
    logging.info("Команда /start была вызвана")
    await update.message.reply_text(
        'Привет! Саджест для поиска терминов работает от 4-х символов.'
    )
    await show_alphabet_menu(update)  # Убедитесь, что эта функция вызывается

async def show_alphabet_menu(callback_query):
    alphabet_buttons = [InlineKeyboardButton(chr(i), callback_data=chr(i)) for i in range(1040, 1072)]  # А-Я
    keyboard = [alphabet_buttons[i:i + 7] for i in range(0, len(alphabet_buttons), 7)]  # Разбиваем на строки
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await callback_query.message.reply_text('Выберите букву:', reply_markup=reply_markup)  # Используем callback_query

async def show_terms_menu(update, context, page=0):
    query_letter = update.callback_query.data.split('_')[0]  # Извлекаем букву
    if not query_letter.isalpha() or len(query_letter) != 1:
        await update.callback_query.answer("Некорректная буква.")
        return
    logging.info(f"Показать меню терминов для буквы: {query_letter}")
    
    terms = [term for term in glossary.keys() if term.startswith(query_letter)]
    logging.info(f"Найденные термины для буквы {query_letter}: {terms}")  # Логирование найденных терминов
    
    if not terms:
        await update.callback_query.answer("Нет терминов на эту букву.")
        return

    # Пагинация
    items_per_page = 9
    start_index = page * items_per_page
    end_index = start_index + items_per_page
    paginated_terms = terms[start_index:end_index]

    buttons = [InlineKeyboardButton(term, callback_data=sanitize_callback_data(term)) for term in paginated_terms]
    buttons.append(InlineKeyboardButton("Назад", callback_data=f"{query_letter}_prev_{page - 1}"))  # Обработчик для кнопки "Назад"
    
    # Добавляем кнопки для навигации
    if end_index < len(terms):
        buttons.append(InlineKeyboardButton("Далее", callback_data=f"{query_letter}_next_{page + 1}"))  # Обработчик для кнопки "Далее"
    if page > 0:
        buttons.append(InlineKeyboardButton("Назад", callback_data=f"{query_letter}_prev_{page - 1}"))

    keyboard = [buttons[i:i + 2] for i in range(0, len(buttons), 2)]  # Разбиваем на строки
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.message.edit_text(f'Термины на букву {query_letter}:', reply_markup=reply_markup)
    await update.callback_query.answer()

async def handle_term_selection(update, context):
    term = update.callback_query.data
    description = glossary.get(term, "Описание не найдено.")
    await update.callback_query.message.reply_text(f"{term}:\n{description}\n___________________________")
    await update.callback_query.answer()

async def handle_back(update, context):
    logging.info("Кнопка 'Назад' нажата")
    await show_alphabet_menu(update.callback_query)  # Передаем callback_query

async def handle_pagination(update, context):
    data = update.callback_query.data.split('_')
    query_letter = data[0]  # Извлекаем букву
    direction = data[1]  # 'next' или 'prev'
    page = int(data[2])  # Номер страницы

    if direction == 'next':
        await show_terms_menu(update, context, page)
    elif direction == 'prev':
        await show_terms_menu(update, context, page - 1)

async def inlinequery(update, context):
    query = update.inline_query.query.lower()

    if len(query) < 4:
        return

    results = []
    count = 0
    for i, (term, description) in enumerate(glossary.items()):
        if query in term.lower():
            results.append(
                InlineQueryResultArticle(
                    id=str(i),
                    title=term,
                    input_message_content=InputTextMessageContent(
                        f"{term}:\n{description}\n___________________________")))
            count += 1
            if count >= 5:
                break
    await update.inline_query.answer(results)

def sanitize_callback_data(data):
    # Заменяем пробелы на подчеркивания
    data = data.replace(" ", "_")
    # Удаляем недопустимые символы
    data = ''.join(c for c in data if c.isalnum() or c in ['_', '-'])
    # Ограничиваем длину до 64 символов
    return data[:64]

def main():
    application = Application.builder().token("7240157972:AAHMY_FnBHE7UZkvkjl3oSfgjM5OtdH6fEM").build()
    
    logging.info("Бот запущен и ожидает обновлений...")
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(show_terms_menu, pattern='^[А-Я]$'))  # Обработчик для букв
    application.add_handler(CallbackQueryHandler(handle_term_selection, pattern='^(?!back).+$'))  # Обработчик для терминов
    application.add_handler(CallbackQueryHandler(handle_back, pattern='^back$'))  # Обработчик для кнопки "Назад"
    application.add_handler(CallbackQueryHandler(handle_pagination, pattern='^[А-Я]_next_[0-9]+|^[А-Я]_prev_[0-9]+$'))  # Обработчик для пагинации
    application.add_handler(InlineQueryHandler(inlinequery))  # Обработчик для поиска по вводу текста
    application.run_polling()

if __name__ == '__main__':
    main()