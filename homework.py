import logging
import os
import time
from http import HTTPStatus

import requests
import telegram
import telegram.ext
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

ERRORS = {
    'KeyError': 'Данного ключа не существует',
    'ResponseStatusError': 'Отсуттсвует подключенеи к API',
    'TypeError': 'Ответ не приведен к нужному Python типу',

}

Old_Status = ''


logging.basicConfig(
    level=logging.INFO,
    filename='main.log',
    format='%(asctime)s, %(levelname)s, %(message)s, %(name)s'
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
logger.addHandler(handler)


def send_message(bot, message):
    if message != 'Статус не изменился':
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logger.info('Сообщение отправлено')


def get_api_answer(current_timestamp):
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    homework_statuses = requests.get(ENDPOINT, headers=HEADERS, params=params)
    if homework_statuses.status_code != HTTPStatus.OK:
        logger.error('Осутствует подключение к API')
        raise ResponseStatusError(ERRORS['ResponseStatusError'])
    return homework_statuses.json()


def check_response(response):
    if not isinstance(response, dict):
        logger.error('Ответ от API не соответсвует нужному типу')
        raise TypeError(ERRORS['TypeError'])
    if response['homeworks'] is None:
        logger.error('Ответ от API не содержит ожиджаемого ключа')
        raise KeyError(ERRORS['KeyError'])
    if not isinstance(response['homeworks'], list):
        logger.error('Ответ от API под ключом homeworks пришел не ввиде списка')
        raise KeyError(ERRORS['KeyError'])
    return response['homeworks']


def parse_status(homework):
    global Old_Status
    homework_name = homework['homework_name']
    homework_status = homework['status']
    verdict = HOMEWORK_STATUSES[homework_status]
    if verdict is None:
        logger.error('такого статуча не существует')
        raise KeyError(ERRORS['KeyError'])
    if verdict == Old_Status:
        logger.debug('Статус не изменился')
        return 'Статус не изменился'
    else:
        Old_Status = verdict
        return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    if not all([PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID],):
        logger.critical('ОТСУТСТВУЮТ ПЕРЕМЕННЫЕ ОКРУЖЕНИЯ')
        return False
    return True


def main():
    """Основная логика работы бота."""
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    while check_tokens():
        try:
            response = get_api_answer(current_timestamp)
            checked_response = check_response(response)
            mes = parse_status(checked_response[0])
            current_timestamp = int(time.time())
            time.sleep(RETRY_TIME)
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            send_message(bot, message)
            time.sleep(RETRY_TIME)
        else:
            send_message(bot, mes)


if __name__ == '__main__':
    main()
