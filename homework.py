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

ERRORS = {
    'KeyError': 'Данного ключа не существует',
    'ResponseStatusError': 'Отсутсвует подключенеи к API',
    'TypeError': 'Ответ не приведен к нужному Python типу',

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
    except Exception:
        raise


def get_api_answer(current_timestamp):
    """Функция получения ответа от API."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    try:
        homework_statuses = requests.get(
            ENDPOINT, headers=HEADERS, params=params
        )
    except Exception:
        raise
    else:
        if homework_statuses.status_code != HTTPStatus.OK:
            raise ResponseStatusError(ERRORS['ResponseStatusError'])
        return homework_statuses.json()


def check_response(response):
    """Функция проверки ответа от API."""
    if not isinstance(response, dict):
        raise TypeError(ERRORS['TypeError'])
    if response['homeworks'] is None:
        raise KeyError(ERRORS['KeyError'])
    if not isinstance(response['homeworks'], list):
        raise KeyError(ERRORS['KeyError'])
    return response['homeworks']


def parse_status(homework):
    """Функция получения статуса домашней работы."""
    if not isinstance(homework, dict):
        raise TypeError(ERRORS['TypeError'])
    if homework['homework_name'] is None:
        raise KeyError(ERRORS['KeyError'])
    homework_name = homework['homework_name']
    if homework['status'] is None:
        raise KeyError(ERRORS['KeyError'])
    homework_status = homework['status']
    verdict = HOMEWORK_STATUSES[homework_status]
    if verdict is None:
        raise KeyError(ERRORS['KeyError'])
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """Проверка переменых окружения."""
    if not all([PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID],):
        return False
    return True


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        logger.critical('ОТСУТСТВУЮТ ПЕРЕМЕННЫЕ ОКРУЖЕНИЯ')
        sys.exit()
    hw_statuses = {}
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    while True:
        try:
            response = get_api_answer(current_timestamp)
            checked_response = check_response(response)
            mes = parse_status(checked_response[0])
            current_timestamp = int(time.time())
            time.sleep(RETRY_TIME)
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logger.error(f'Сбой в работе программы: {error}')
            try:
                send_message(bot, message)
                logger.info('Сообщение отправлено')
            except Exception as b_err:
                logger.error(f'Сбой при отправке сообщений: {b_err}')
            finally:
                time.sleep(RETRY_TIME)
        else:
            status = checked_response[0]['status']
            hw_name = checked_response[0]['homework_name']
            if hw_name not in hw_statuses.keys():
                hw_statuses[hw_name] = ''
            if hw_statuses[hw_name] != status:
                hw_statuses[hw_name] = status
                send_message(bot, mes)
                logger.info('Сообщение отправлено')
            else:
                logger.debug('Статус не изменился')


if __name__ == '__main__':
    main()
