import telebot  # API для работы с Telegram
from auth import key # В данном файле должна лежать одна переменная key с токеном авторизации бота
from telebot import types # Имопорт типов из API

import time # Для работы с временем
import datetime # Для работы с временем
import schedule # Планировщимк событий
from multiprocessing.context import Process # Библиотека для огранизации многозадачности

from random import choice # Для случайного выбора звонков

from utils import file_system, tools # Файлы с дополнительными функциями


def timeReg(time, user):
    # Назначение задач по дням недели (для вызова в другой функции)
    # Аргументы: время и id пользователя
    schedule.clear()
    schedule.every().monday.at(str(time)).do(sendCall, userID=user)
    schedule.every().tuesday.at(str(time)).do(sendCall, userID=user)
    schedule.every().wednesday.at(str(time)).do(sendCall, userID=user)
    schedule.every().thursday.at(str(time)).do(sendCall, userID=user)
    schedule.every().friday.at(str(time)).do(sendCall, userID=user)

def journal():
    # Обновление планировщика
    for user_id in file_system.read('users'):
        user = file_system.read('users')[user_id]
        for grade in tools.times:
            if user["grade"] == grade:
                for time in tools.times[grade]:
                    hour = time.split(':')[0]
                    minute = time.split(':')[1]
                    lesson = datetime.timedelta(hours=int(hour))+datetime.timedelta(minutes=int(minute))+datetime.timedelta(minutes=1)
                    minute1 = datetime.timedelta(hours=int(hour))+datetime.timedelta(minutes=int(minute))
                    minute5 = datetime.timedelta(hours=int(hour))+datetime.timedelta(minutes=int(minute))+datetime.timedelta(minutes=-4)
                    endlesson = datetime.timedelta(hours=int(hour))+datetime.timedelta(minutes=int(minute))+datetime.timedelta(minutes=46)
                    if user["5min"] == "1":
                        timeReg(tools.add0(str(minute5)[:-3]), user_id)
                    if user["1min"] == "1":
                        timeReg(tools.add0(str(minute1)[:-3]), user_id)
                    if user["0min"] == "1":
                        timeReg(tools.add0(str(lesson)[:-3]), user_id)
                    if user["end"] == "1":
                        timeReg(tools.add0(str(endlesson)[:-1]), user_id)


def keyboardMaker(keyboardName):
    # Создаёт клавиатуру по списку кнопок из файла keyboards
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    for item in keyboardName:
        keyboard.add(item)
    return keyboard

def keyboardMakerSettings(userID):
    # Создаёт клавиатуру с индикацией выбора опций
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    keys = ["5min", "1min", "0min", "end"]
    i = 0
    for item in file_system.read('keyboards')['MINUTES_MENU']['buttons']:
        if file_system.read('users')[str(userID)][keys[i]] == "0":
            keyboard.add(item + "❌")
        elif file_system.read('users')[str(userID)][keys[i]] == "1":
            keyboard.add(item + "✅")
        i += 1
    keyboard.add(file_system.read('messages')['CANCEL'])
    return keyboard


# Инициализация бота
bot = telebot.TeleBot(key)

# Обработка команды help
@bot.message_handler(commands=['help'])
def send_help(message):
    bot.send_message(message.from_user.id, file_system.read('messages')['REGISTER_GREETING'])

# Обработка команды start (запускается при первом запуске бота пользоватлем)
@bot.message_handler(commands=['start'])
def start_message(message):
    if str(message.from_user.id) in file_system.read('users') and file_system.read('users')[str(message.from_user.id)]['grade'] != "0":
        mainMenu(message)
    elif str(message.from_user.id) in file_system.read('users') and file_system.read('users')[str(message.from_user.id)]['grade'] == "0":
        bot.send_message(message.from_user.id, file_system.read('messages')['REGISTER_GREETING'])
        bot.send_message(message.from_user.id, file_system.read('messages')['REGISTER_PUSH'], reply_markup=keyboardMaker(file_system.read('keyboards')['REGISTER_PUSH']['buttons']))
        bot.register_next_step_handler(message, subscribe)
    elif not str(message.from_user.id) in file_system.read('users'):
        file_system.new_user(message.from_user.id)
        bot.send_message(message.from_user.id, file_system.read('messages')['REGISTER_GREETING'])
        bot.send_message(message.from_user.id, file_system.read('messages')['REGISTER_PUSH'], reply_markup=keyboardMaker(file_system.read('keyboards')['REGISTER_PUSH']['buttons']))
        bot.register_next_step_handler(message, subscribe)

# Обработка подписки/отписки на звонки
def subscribe(message):
    try:
        if message.text == file_system.read('keyboards')['REGISTER_PUSH']['buttons'][0]:
            bot.send_message(message.from_user.id, file_system.read('messages')['REGISTER_WRONG_CLASS'], reply_markup=keyboardMaker(file_system.read('keyboards')['REGISTER_CLASS']['buttons']))
            bot.register_next_step_handler(message, registerClass)
        elif message.text == file_system.read('keyboards')['REGISTER_PUSH']['buttons'][1]:
            file_system.update_user(str(message.from_user.id), 'grade', "0")
            bot.send_message(message.from_user.id, file_system.read('messages')['REGISTER_ERROR'])
            journal()
        elif message.text == file_system.read('keyboards')['MENU']['buttons'][0]:
            bot.send_message(message.from_user.id, file_system.read('messages')['REGISTER_WRONG_CLASS'], reply_markup=keyboardMaker(file_system.read('keyboards')['REGISTER_CLASS']['buttons']))
            bot.register_next_step_handler(message, registerClass)
    except:
        bot.send_message(message.from_user.id, file_system.read('messages')['ERROR'])

# Запись подписки в базу и регистрация в планировщике
def registerClass(message):
    file_system.update_user(str(message.from_user.id), 'grade', str(message.text))
    bot.send_message(message.from_user.id, file_system.read('messages')['REGISTER_COMPLETE'])
    journal()
    mainMenu(message)

# Главное меню
def mainMenu(message):
    bot.send_message(message.from_user.id, file_system.read('messages')['MAIN_MENU'], reply_markup=keyboardMaker(file_system.read('keyboards')['MENU']['buttons']))

# Настрока времени уведомлений
def settings(message):
    string = message.text[:-2]
    dict = {"За 5 минут:": "5min", "За 1 минуту:": "1min", "Во время звонка:": "0min", "В конце урока:": "end"}
    if string in dict:
        if file_system.read('users')[str(message.from_user.id)][dict[string]] == "0":
            file_system.update_user(str(message.from_user.id), dict[string], "1")
        elif file_system.read('users')[str(message.from_user.id)][dict[string]] == "1":
            file_system.update_user(str(message.from_user.id), dict[string], "0")
        bot.send_message(message.from_user.id, file_system.read('messages')["SETTINGS_CHANGED"], reply_markup=keyboardMakerSettings(str(message.from_user.id)))
        bot.register_next_step_handler(message, settings)
    if message.text == file_system.read('messages')['CANCEL']:
        mainMenu(message)

# Обработка текстовых событий
@bot.message_handler(content_types=['text'])
def get_text_messages(message):
    if message.text == file_system.read('keyboards')['MENU']['buttons'][1]:
        bot.send_message(message.from_user.id, file_system.read('messages')["SETTINGS"], reply_markup=keyboardMakerSettings(str(message.from_user.id)))
        bot.register_next_step_handler(message, settings)
    if message.text == file_system.read('keyboards')['MENU']['buttons'][0]:
        bot.send_message(message.from_user.id, file_system.read('messages')['REGISTER_PUSH'], reply_markup=keyboardMaker(file_system.read('keyboards')['REGISTER_PUSH']['buttons']))
        bot.register_next_step_handler(message, subscribe)
    if message.text == file_system.read('messages')['CANCEL']:
        mainMenu(message)

# Отправка сообщения о звонке
def sendCall(userID):
    message = choice(file_system.read('messages')['TO_LESSON'])
    bot.send_message(userID, message)
    file_system.log("log", f"Пользователю {userID} отправлено сообщение {message} в {datetime.datetime.now()}")

# Настройка многозадачности
journal()
class ScheduleMessage():
    def try_send_schedule():
        while True:
            schedule.run_pending()
            time.sleep(1)

    def start_process():
        p1 = Process(target=ScheduleMessage.try_send_schedule, args=())
        p1.start()

if __name__ == '__main__':

    ScheduleMessage.start_process()
    try:
        bot.polling(none_stop=True)
    except:
        pass
