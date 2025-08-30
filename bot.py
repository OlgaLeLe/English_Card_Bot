import random
from telebot import types, TeleBot, custom_filters
from telebot.storage import StateMemoryStorage
from telebot.handler_backends import State, StatesGroup

from db import (
    get_random_word,
    get_variants,
    add_word,
    delete_word,
    count_user_words
)

print('Start telegram bot...')

state_storage = StateMemoryStorage()
token_bot = '7974218001:AAFh6z3Hnd7uLs-HjwgTQ1XEtYNIkLa2NTc'  
bot = TeleBot(token_bot, state_storage=state_storage)

known_users = []
userStep = {}
buttons = []


def show_hint(*lines):
    return '\n'.join(lines)


def show_target(data):
    return f"{data['target_word']} -> {data['translate_word']}"


class Command:
    ADD_WORD = 'Добавить слово ➕'
    DELETE_WORD = 'Удалить слово 🔙'
    NEXT = 'Дальше ⏭️'


class MyStates(StatesGroup):
    target_word = State()
    translate_word = State()
    another_words = State()


def get_user_step(uid):
    if uid in userStep:
        return userStep[uid]
    else:
        known_users.append(uid)
        userStep[uid] = 0
        print("New user detected, who hasn't used \"/start\" yet")
        return 0


# Приветственное сообщение + карточки
@bot.message_handler(commands=['cards', 'start'])
def create_cards(message):
    cid = message.chat.id
    if cid not in known_users:
        known_users.append(cid)
        userStep[cid] = 0
        greeting = (
            "Привет 👋 Давай попрактикуемся в английском языке.\n"
            "Ты можешь тренироваться в удобном темпе.\n\n"
            "Используй инструменты:\n"
            "➕ Добавить слово\n"
            "🔙 Удалить слово\n\n"
            "Ну что, начнём ⬇️"
        )
        bot.send_message(cid, greeting)

    markup = types.ReplyKeyboardMarkup(row_width=2)

    global buttons
    buttons = []

    # Берём слово из базы
    target_data = get_random_word(cid)
    target_word = target_data['eng_word']
    translate = target_data['rus_word']

    # Варианты
    others = get_variants(target_word)
    buttons = [types.KeyboardButton(word) for word in others]

    # Добавляем кнопки управления
    next_btn = types.KeyboardButton(Command.NEXT)
    add_word_btn = types.KeyboardButton(Command.ADD_WORD)
    delete_word_btn = types.KeyboardButton(Command.DELETE_WORD)
    buttons.extend([next_btn, add_word_btn, delete_word_btn])

    markup.add(*buttons)

    greeting = f"Выбери перевод слова:\n🇷🇺 {translate}"
    bot.send_message(message.chat.id, greeting, reply_markup=markup)
    bot.set_state(message.from_user.id, MyStates.target_word, message.chat.id)

    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        data['target_word'] = target_word
        data['translate_word'] = translate


@bot.message_handler(func=lambda message: message.text == Command.NEXT)
def next_cards(message):
    create_cards(message)


@bot.message_handler(func=lambda message: message.text == Command.DELETE_WORD)
def delete_word_handler(message):
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        delete_word(message.chat.id, data['target_word'])
        bot.send_message(message.chat.id, f"Слово {data['target_word']} удалено из твоей базы ✅")


@bot.message_handler(func=lambda message: message.text == Command.ADD_WORD)
def add_word_handler(message):
    cid = message.chat.id
    bot.send_message(cid, "Напиши новое слово в формате: `english - русский`")
    userStep[cid] = 1  # ждём ввод слова


@bot.message_handler(func=lambda message: True, content_types=['text'])
def message_reply(message):
    cid = message.chat.id
    text = message.text

    # Если пользователь вводит новое слово
    if userStep.get(cid) == 1:
        try:
            eng, rus = text.split('-')
            eng, rus = eng.strip(), rus.strip()
            add_word(cid, eng, rus)
            total = count_user_words(cid)
            bot.send_message(cid, f"Слово '{eng} - {rus}' добавлено ✅\nТеперь у тебя {total} слов.")
        except Exception:
            bot.send_message(cid, "❌ Неверный формат. Введи так: `word - перевод`")
        userStep[cid] = 0
        return

    # Проверка ответа
markup = types.ReplyKeyboardMarkup(row_width=2)
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        target_word = data['target_word']
        if text == target_word:
            hint = show_target(data)
            hint_text = ["Отлично!❤️", hint]
            hint = show_hint(*hint_text)
        else:
            hint = show_hint("Допущена ошибка!",
                             f"Попробуй ещё раз 🇷🇺 {data['translate_word']}")

    markup.add(*buttons)
    bot.send_message(message.chat.id, hint, reply_markup=markup)


bot.add_custom_filter(custom_filters.StateFilter(bot))

bot.infinity_polling(skip_pending=True)

