import logging
import os
import sys
import time
from http import HTTPStatus

import requests
import telegram
from dotenv import load_dotenv
from exceptions import ResponseStatusError

load_dotenv()


PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}

HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


logging.basicConfig(
    level=logging.INFO,
    filename='main.log',
    format='%(asctime)s, %(levelname)s, %(message)s, %(name)s, %(lineno)s'
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
logger.addHandler(handler)


def send_message(bot, message):
    """Функция отправки сообщения ботом."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
    except telegram.error.TelegramError as err:
        raise err


def get_api_answer(current_timestamp):
    """Функция получения ответа от API."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    try:
        homework_statuses = requests.get(
            ENDPOINT, headers=HEADERS, params=params
        )
        if homework_statuses.status_code != HTTPStatus.OK:
            raise ResponseStatusError
        return homework_statuses.json()
    except requests.exceptions.RequestException as err:
        raise err


def check_response(response):
    """Функция проверки ответа от API."""
    if not isinstance(response, dict):
        raise TypeError
    if 'homeworks' not in response.keys():
        raise KeyError
    if response['homeworks'] is None:
        raise ValueError
    if not isinstance(response['homeworks'], list):
        raise TypeError
    return response['homeworks']


def parse_status(homework):
    """Функция получения статуса домашней работы."""
    if not isinstance(homework, dict):
        raise TypeError
    if 'homework_name' not in homework.keys():
        raise KeyError
    if homework['homework_name'] is None:
        raise ValueError
    homework_name = homework['homework_name']
    if 'status' not in homework.keys():
        raise KeyError
    if homework['status'] is None:
        raise ValueError
    homework_status = homework['status']
    if homework_status not in HOMEWORK_STATUSES.keys():
        raise KeyError
    verdict = HOMEWORK_STATUSES[homework_status]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """Проверка переменых окружения."""
    return all([PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID],)


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        logger.critical('ОТСУТСТВУЮТ ПЕРЕМЕННЫЕ ОКРУЖЕНИЯ')
        sys.exit()
    hw_old = {'name': '', 'status': ''}
    hw_now = {'name': '', 'status': ''}
    old_error = ''
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    while True:
        try:
            response = get_api_answer(current_timestamp)
            checked_response = check_response(response)
            mes = parse_status(checked_response[0])
            current_timestamp = int(time.time())
            hw_now = {
                'name': checked_response[0]['homework_name'],
                'status': checked_response[0]['status'],
            }
            if hw_now != hw_old:
                hw_old = hw_old
                send_message(bot, mes)
                logger.info('Сообщение отправлено')
            else:
                logger.debug('Статус не изменился')
            time.sleep(RETRY_TIME)
        except telegram.error as b_err:
            logger.error(f'Сбой при отправке сообщений: {b_err}')
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logger.error(f'Сбой в работе программы: {error}')
            if old_error != (f'{error}'):
                old_error = (f'{error}')
                send_message(bot, message)
                logger.info('Сообщение отправлено')
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
