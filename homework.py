import os
import requests
import logging
import time

from dotenv import load_dotenv

from telegram.ext import Updater, MessageHandler, Filters, CommandHandler
import telegram

load_dotenv()

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

DOTENV = {
    'PRACTICUM_TOKEN': PRACTICUM_TOKEN,
    'TELEGRAM_TOKEN': TELEGRAM_TOKEN,
    'TELEGRAM_CHAT_ID': TELEGRAM_CHAT_ID,
}

RETRY_PERIOD =  10 #600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}

logging.basicConfig(
    format='%(asctime)s - [%(levelname)s] - %(message)s',
    level=logging.DEBUG)


HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def check_tokens():
    for name, token in DOTENV.items():
        if token is None:
            logging.critical(
                "Отсутствует обязательная переменная окружения: "
                f"{name}\nПрограмма принудительно остановлена.")
            return False
    return True



def send_message(bot, message):
    bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)


def get_api_answer(timestamp):
    params = {'from_date': timestamp}
    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=params).json()
        return response
    except Exception as Error:
        logging.error(f"Ошибка выполнения запроса: ({Error})")
        return None


def check_response(response):
    if (response is not None):
        # Тут еще другие проверки будут
        return True
    else:
        return False


def parse_status(homework):
    homework_name = homework.get('homework_name')
    status = homework.get('status')
    verdict = HOMEWORK_VERDICTS.get(status)
    if verdict is None:
        logging.error(f'Неизвестный статус работы: {status}')
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        return
    
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())
    while True:
        try:
            response = get_api_answer(timestamp)
            timestamp = int(time.time())
            if check_response(response):
                homeworks = list(response.get('homeworks'))
                if not homeworks:
                    logging.debug('Обновлений не найдено')
                else:
                    for homework in homeworks:
                        message = parse_status(homework)
                        send_message(bot, message)

        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            send_message(bot, message)
            break
        time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
