import os
import sys
import requests
import logging
import time
import telegram

from dotenv import load_dotenv
from requests import exceptions
from http import HTTPStatus

load_dotenv()

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

DOTENV = {
    'PRACTICUM_TOKEN': PRACTICUM_TOKEN,
    'TELEGRAM_TOKEN': TELEGRAM_TOKEN,
    'TELEGRAM_CHAT_ID': TELEGRAM_CHAT_ID,
}

RETRY_PERIOD = 10 * 60
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
    """Проверка наличия необходимых токенов в .env."""
    return all([PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID])


def send_message(bot, message):
    """Отправка сообщения в чат."""
    try:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
        logging.debug(f'Отправлено сообщение: {message}')
    except Exception as Error:
        logging.error(f'Ошибка отправки сообщения: ({Error})')


def get_api_answer(timestamp):
    """Отпрака запроса на API домашки. Возвращает ответ от API."""
    params = {'from_date': timestamp}
    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=params)
    except Exception as Error:
        logging.error(f'Ошибка выполнения запроса: ({Error})')
        return None
    if response.status_code != HTTPStatus.OK:
        logging.error(f'Ошибка. Код ответа: {response.status_code}')
        raise exceptions.ConnectionError(
            f'Ошибка. Код ответа: {response.status_code}'
        )
    return response.json()


def check_response(response):
    """Проверка корректности полученного от API домашки ответа."""
    if not isinstance(response, dict):
        raise TypeError('Переменная не соответствует типу dict')
    homeworks = response.get('homeworks')
    if not isinstance(homeworks, list):
        raise TypeError('Тип преченя домашних работ не является списком')
    return True


def parse_status(homework):
    """Достает из словаря homework данные о статусе проверки дз."""
    homework_name = homework.get('homework_name')
    if (homework_name is None):
        raise KeyError('В ответе API нет названия домашки')
    status = homework.get('status')
    if (status is None):
        raise KeyError('В ответе API нет статуса домашки')
    verdict = HOMEWORK_VERDICTS.get(status)
    if verdict is None:
        raise KeyError(f'Неизвестный статус работы: {status}')
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    last_exception = None
    if not check_tokens():
        logging.critical(
            'Отсутствует обязательная переменная окружения'
            'Программа принудительно остановлена.')
        sys.exit()
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = 0
    while True:
        try:
            response = get_api_answer(timestamp)
            timestamp = int(time.time())
            if check_response(response):
                homeworks = list(response.get('homeworks'))
                if len(homeworks) == 0:
                    logging.debug('Обновлений не найдено')
                else:
                    for homework in homeworks:
                        message = parse_status(homework)
                        send_message(bot, message)
        except Exception as error:
            if (error != last_exception):
                message = f'Сбой в работе программы: {error}'
                send_message(bot, message)
                last_exception = error
        time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
