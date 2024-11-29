# Exchange Bot
Exchange Bot — это телеграм-бот для автоматизации расчета обмена валют по текущим биржевым курсам на основе данных из источника app.exchangerate-api.com.
Этот проект включает в себя всё необходимое для быстрого развертывания на VPS.

Вам понадобится:

`API-ключ из app.exchangerate-api.com`

`BOT-Token вашего ТГ-бота`

## Установка и запуск
Следуйте приведённым ниже шагам, чтобы установить и запустить бота на вашем сервере.

### Шаг 1: Подготовка
Убедитесь, что ваш сервер соответствует следующим требованиям:

**Операционная система:** `Linux (Ubuntu/Debian)`

**Python:** `3.8 или выше`

**Доступ к интернету**

**Установленные пакеты:** `git, python3-pip`

Если что-то из этого не установлено, скрипт сделает это за вас.

### Шаг 2: Скачивание и установка
1. Зайдите в терминал вашего сервера.
2. Скопируйте и выполните следующий набор команд:
### Скачиваем установочный скрипт
````
curl -O https://raw.githubusercontent.com/indie-master/exchange_bot/main/setup_exchange_bot.sh
````

### Делаем скрипт исполняемым
````
chmod +x setup_exchange_bot.sh
````

### Запускаем скрипт
````
./setup_exchange_bot.sh
````

### Шаг 3: Конфигурация
Во время выполнения скрипта вас попросят ввести два параметра:

`API_KEY` — ключ для подключения к Telegram API.

`BOT_TOKEN` — токен вашего Telegram-бота.

Эти данные будут автоматически сохранены в файл `.env`

### Шаг 4: Запуск
После завершения скрипта бот запустится автоматически.

Для проверки его работы, откройте файл логов:
````
tail -f bot.log
````
Убедитесь, что бот активен и работает корректно.

## Дополнительно
### Перезапуск бота
Если вам нужно перезапустить бота, выполните следующие команды:
````
cd ~/exchange_bot
source venv/bin/activate`
nohup python3 exchange_bot.py > bot.log 2>&1 &
````

### Остановка бота
Для остановки процесса найдите его ID и завершите:
````
ps aux | grep exchange_bot.py
kill <PROCESS_ID>
````

## Настройка через Systemd
### 1. Создайте файл сервиса:
Откройте редактор и создайте новый файл:

````
sudo nano /etc/systemd/system/exchange_bot.service
````

Добавьте следующую конфигурацию:
````
[Unit]
Description=Exchange Bot
After=network.target

[Service]
User=<ваш_пользователь>
WorkingDirectory=/<ваш_пользователь>/exchange_bot
ExecStart=/<ваш_пользователь>/exchange_bot/venv/bin/python3 exchange_bot.py
Restart=always
EnvironmentFile=/<ваш_пользователь>/exchange_bot/.env

[Install]
WantedBy=multi-user.target
````

Замените `<ваш_пользователь>` на имя вашего пользователя.

### 2. Перезагрузите Systemd и активируйте сервис:

````
sudo systemctl daemon-reload
sudo systemctl enable exchange_bot
````

### 3. Запустите бота:

````
sudo systemctl start exchange_bot
````

### 4. Рестарт после изменений:
После изменения токена или кода перезапустите сервис:

````
sudo systemctl restart exchange_bot
````

### 5. Проверка статуса:
Убедитесь, что бот работает:

````
sudo systemctl status exchange_bot
````

Настройка через Systemd автоматизирует перезапуск и упрощает управление ботом.