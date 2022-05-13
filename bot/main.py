import os
import time
import news

from settings import Settings as config

from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.utils import executor

bot_token = config.TG_BOT_TOKEN

bot = Bot(token=bot_token)
dp = Dispatcher(bot)


@dp.message_handler(commands=['start', 'commands', 'help'])
async def start_command(message: types.Message):
    buttons = [
        types.InlineKeyboardButton(text='Все новости', callback_data='all_news'),
        types.InlineKeyboardButton(text='Категории', callback_data='category_list')
    ]
    keyboard = types.InlineKeyboardMarkup(row_width=3, resize_keyboard=True)
    keyboard.add(*buttons)
    await message.answer('Что тебя интересует?', reply_markup=keyboard)


@dp.callback_query_handler(text='all_news')
async def send_all_news_callback(call: types.CallbackQuery):
    posts = news.get_all_posts()
    messages = news.create_message_posts(posts)

    for num, message in enumerate(messages):
        if num % 5 == 0:
            time.sleep(2)
        if message.img:
            await call.message.answer_photo(photo=message.img, caption=message.text, parse_mode='Markdown')
        else:
            await call.message.answer(message.text, parse_mode='markdown')

    await call.answer()


@dp.callback_query_handler(text='category_list')
async def send_category_list(call: types.CallbackQuery):
    buttons = [
        types.InlineKeyboardButton(text='Образование', callback_data='education'),
        types.InlineKeyboardButton(text='Наука', callback_data='science'),
        types.InlineKeyboardButton(text='Развлечения', callback_data='fun'),
        types.InlineKeyboardButton(text='IT', callback_data='it'),
        types.InlineKeyboardButton(text='Космос', callback_data='space'),
        types.InlineKeyboardButton(text='Повседневная жизнь', callback_data='life'),
        types.InlineKeyboardButton(text='Политика', callback_data='politics'),
        types.InlineKeyboardButton(text='Кулинария', callback_data='cooking'),
        types.InlineKeyboardButton(text='Садовничество', callback_data='gardening'),
        types.InlineKeyboardButton(text='Личная продуктивность', callback_data='personal_productivity')
    ]
    keyboard = types.InlineKeyboardMarkup(row_width=3, resize_keyboard=True)
    keyboard.add(*buttons)
    await call.message.answer(text='Выбери категорию: ', reply_markup=keyboard)
    await call.answer()


@dp.callback_query_handler(text=['education', 'science', 'fun', 'it', 'space', 'life', 'politics', 'cooking',
                                 'gardening', 'personal_productivity'])
async def send_categories_news(call: types.CallbackQuery):
    categories = {
        'education': 'Образование',
        'science': 'Наука',
        'fun': 'Развлечения',
        'it': 'IT',
        'space': 'Космос',
        'life': 'Повседневная жизнь',
        'politics': 'Политика',
        'cooking': 'Кулинария',
        'gardening': 'Садовничество',
        'personal_productivity': 'Личная продуктивность'
    }

    posts = news.get_category_posts(categories[call.data])
    messages = news.create_message_posts(posts)

    for num, message in enumerate(messages):
        if num % 5 == 0:
            time.sleep(2)
        if message.img:
            await call.message.answer_photo(photo=message.img, caption=message.text, parse_mode='Markdown')
        else:
            await call.message.answer(message.text, parse_mode='markdown')

    await call.answer()


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
