import telebot
from telebot import types
from telebot.types import InlineKeyboardButton
from tinydb import TinyDB, Query

bot = telebot.TeleBot()
db = TinyDB('db.json')
group_table = db.table('groups')
admins_table = db.table('admins')

start_markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
start_markup.row('', 'Меню', '')
start_markup.row('', 'Инфо', '')

admin_start_markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
admin_start_markup.row('', 'Добавить администратора', '')
admin_start_markup.row('', 'Добавить группу', '')
admin_start_markup.row('', 'Опубликовать пост', '')
admin_start_markup.row('', 'Меню', '')
admin_start_markup.row('', 'Инфо', '')

reject_markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
reject_markup.row('', 'Отмена', '')


def default_markup(message):
    if is_admin(message):
        return admin_start_markup
    else:
        return start_markup


def info(message):
    print(f'[INFO] {message}')


def error(message):
    print(f'[ERROR] {message}')


def warn(message):
    print(f'[WARNING] {message}')


def is_admin(message):
    user = Query()
    return len(admins_table.search(user.id == message.chat.id)) > 0


def welcome_message(message):
    global start_markup
    welcome_msg = '''
Привет, я простой бот который может упростить твою работу.

Просто добавь меня в группу (канал) и сделай администратором.

Если не знаешь айди группы, просто перешли мне сообщение из нее, я подскажу :)
'''
    bot.send_message(message.chat.id, welcome_msg, reply_markup=default_markup(message))


def get_message_forward(message):
    if message.forward_from_chat is not None:
        return message.forward_from_chat
    elif message.forward_from is not None:
        return message.forward_from
    else:
        return None


def get_is_group(message):
    forward = get_message_forward(message)
    if forward:
        if forward.type == 'channel':
            return True
        else:
            return False


def is_forwarded(message):
    if message.forward_from_chat is not None:
        return True
    elif message.forward_from is not None:
        return True
    return False


def get_chat_id(message, only_channels=False):
    if message.forward_from_chat is not None:
        return message.forward_from_chat.id
    elif message.forward_from is not None:
        return message.forward_from.id
    if not only_channels:
        return message.chat.id


def send_to_group(id, message):
    file_id = message.document.file_id
    file = bot.get_file(file_id)
    downloaded_file = bot.download_file(file.file_path)
    try:
        bot.send_photo(id, downloaded_file)
        bot.send_document(id, file_id)
    except Exception as e:
        bot.send_message(message.chat.id, str(e))
        error(e)


def add_admin_second(message):
    if message.text == 'Отмена':
        bot.send_message(message.chat.id, 'Отмена', reply_markup=default_markup(message))
        return
    try:
        user = Query()
        if is_forwarded(message):
            already_has = len(admins_table.search(user.id == int(get_chat_id(message)))) > 0
            if already_has:
                bot.send_message(message.chat.id, 'Уже есть такой администратор', reply_markup=default_markup(message))
                return
            admins_table.insert({'id': int(get_chat_id(message))})
            bot.send_message(message.chat.id, 'Успешно добавили администратора (по пересланному сообщению)',
                             reply_markup=default_markup(message))
        else:
            if message.text.isdigit():
                already_has = len(admins_table.search(user.id == int(message.text))) > 0
                if already_has:
                    bot.send_message(message.chat.id, 'Уже есть такой администратор',
                                     reply_markup=default_markup(message))
                    return
                admins_table.insert({'id': int(message.text)})
                bot.send_message(message.chat.id, 'Успешно добавили администратора (прямое указание ID пользователя)',
                                 reply_markup=default_markup(message))
            else:
                bot.send_message(message.chat.id, 'Проверьте введеное значение', reply_markup=default_markup(message))
    except Exception as e:
        error(e)
        bot.send_message(message.chat.id, 'Что-то пошло не так, обратитесь к администратору бота',
                         reply_markup=default_markup(message))


@bot.message_handler(func=lambda message: message.text in ['Добавить администратора'])
def add_admin(message):
    if is_admin(message):
        sent = bot.send_message(message.chat.id, 'Введите айди пользователя или перешлите его сообщение',
                                reply_markup=reject_markup)
        bot.register_next_step_handler(sent, add_admin_second)
        pass
    else:
        bot.send_message(message.chat.id, 'Ты не админ этого бота, извинити :с', reply_markup=default_markup(message))


def add_group_third(message, data):
    if message.text == 'Отмена':
        bot.send_message(message.chat.id, 'Отмена', reply_markup=default_markup(message))
        return
    if message.text:
        group = Query()
        already_has = len(group_table.search(group.id == int(data))) > 0
        if already_has:
            bot.send_message(message.chat.id, 'Группа уже есть в моем списке', reply_markup=default_markup(message))
            return
        group_table.insert({'id': int(data), 'name': message.text})
        bot.send_message(message.chat.id, 'Успешно добавили группу', reply_markup=default_markup(message))
    else:
        bot.send_message(message.chat.id, 'Проверь название группы и начни сначала',
                         reply_markup=default_markup(message))


def add_group_second(message):
    if message.text == 'Отмена':
        bot.send_message(message.chat.id, 'Отмена', reply_markup=default_markup(message))
        return
    is_forwarded_group = get_is_group(message)
    if is_forwarded_group:
        data = get_message_forward(message).id
        sent = bot.send_message(message.chat.id,
                                'А теперь введи название группы. Можно любое, по нему ты будешь понимать, куда отправляешь сообщение',
                                reply_markup=reject_markup)
        bot.register_next_step_handler(sent, add_group_third, data)
    else:
        data = message.text
        sent = bot.send_message(message.chat.id,
                                'А теперь введи название группы. Можно любое, по нему ты будешь понимать, куда отправляешь сообщение',
                                reply_markup=reject_markup)
        bot.register_next_step_handler(sent, add_group_third, data)


@bot.message_handler(func=lambda message: message.text in ['Добавить группу'])
def add_group(message):
    if is_admin(message):
        sent = bot.send_message(message.chat.id, 'Введите айди группы или перешлите из неё сообщение.',
                                reply_markup=reject_markup)
        bot.register_next_step_handler(sent, add_group_second)
        pass
    else:
        bot.send_message(message.chat.id, 'Ты не админ этого бота, извинити :с', reply_markup=default_markup(message))


global_current_file = None


def second_send_to_groups(message):
    global global_current_file
    if message.text == 'Отмена':
        bot.send_message(message.chat.id, 'Отмена', reply_markup=default_markup(message))
        return
    if message.document:
        global_current_file = message
        all_groups = group_table.all()
        groups_markup = types.InlineKeyboardMarkup(keyboard=None)
        groups_markup.row_width = 4
        for group in all_groups:
            groups_markup.add(InlineKeyboardButton(group['name'], callback_data=group['id']))
        groups_markup.add(InlineKeyboardButton('Все', callback_data='all'))
        bot.send_message(message.chat.id, 'Отлично, выбери группу (или все), куда хочешь отправить фото',
                         reply_markup=groups_markup)
    else:
        bot.send_message(message.chat.id, 'Кажется файл не тот или его вообще нет, попробуй сначала',
                         reply_markup=default_markup(message))


@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    global global_current_file
    if call.data != "all":
        bot.edit_message_reply_markup(message_id=call.message.id, chat_id=call.message.chat.id, reply_markup=None)
        if global_current_file is not None:
            bot.answer_callback_query(call.id, "Отлично, отправлю сюда")
            send_to_group(id=call.data, message=global_current_file)
            global_current_file = None
            bot.send_message(call.message.chat.id, 'Успешно отправлено', reply_markup=default_markup(call.message))
        else:
            bot.send_message(call.message.id, 'Кажется, что-то пошло не так. Обратитесь к администратору бота',
                             reply_markup=default_markup(call.message))

    elif call.data == "all":
        bot.edit_message_reply_markup(message_id=call.message.id, chat_id=call.message.chat.id, reply_markup=None)
        bot.answer_callback_query(call.id, "Отлично, отправлю во все")
        all_groups = group_table.all()
        for group in all_groups:
            send_to_group(id=group['id'], message=global_current_file)
            bot.send_message(call.message.id, 'Отправка завершена', reply_markup=default_markup(call.message))


@bot.message_handler(func=lambda message: message.text in ['Опубликовать пост'])
def send_to_groups(message):
    has_any_groups = len(group_table.all()) > 0
    if has_any_groups:
        sent = bot.send_message(message.chat.id, 'Пришли мне не сжатое изображение, которое хочешь опубликовать',
                                reply_markup=reject_markup)
        bot.register_next_step_handler(sent, second_send_to_groups)
    else:
        bot.send_message(message.chat.id, 'Нет добавленных групп. Добавьте хотя бы одну',
                         reply_markup=default_markup(message))


@bot.message_handler(commands=['start', 'help', 'menu'])
def send_welcome(message):
    welcome_message(message)


@bot.message_handler(func=lambda message: message.text in ['Меню'])
def send_welcome(message):
    welcome_message(message)


@bot.message_handler(func=lambda message: True)
def echo_all(message):
    info(message)
    try:
        bot.send_message(message.chat.id, f'Айди этой группы: {message.forward_from_chat.id}')
    except Exception as e:
        bot.send_message(message.chat.id, message.text, reply_markup=default_markup(message))
        error(e)


bot.infinity_polling()
