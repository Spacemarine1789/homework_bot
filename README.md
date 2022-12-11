# homework_bot
Это учебный проект Яндекс.Практикума, в котором мы писали telegram-бота, который взаимодействет с API яндекс практикума и присылает сообщения о статусе текущей домагей работы. В этом проекте использована библиотека python-telegram-bot.

Для установки необходимо:
1. Клонировать проект в нужной папку

2. Создать и запустить виртуальное окружение:
При работе на Windows при использовании терминала Git Bash выполните следующие команды:
```
cd homework_bot
```
команда для перехода в папку с проетком
```
python -m venv venv
source venv/Scripts/activate
python3 -m pip install --upgrade pip
```

3. Установить зависимости:
```
pip install -r requirements.txt
```

4. Создайте и заполните файл ```.env```:
```
TELEGRAM_TOKEN=*********
PRACTICUM_TOKEN=*********
TELEGRAM_CHAT_ID=*********
```
Вместо звездочек должны быть токены для телеграм бота и api практикума, а также id чата, кому будет присылать сообщение бот.

5. Запустите файл ```homework.py```. 
Пока этот файл будет запущен телеграмм бот будет работать. Весь проект можно запустить на удаленный сервер и запусть бота там.
