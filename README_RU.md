# Exchange Bot
Exchange Bot — это телеграм-бот для автоматизации расчета обмена валют по текущим биржевым курсам на основе данных из источника app.exchangerate-api.com.
Этот проект включает в себя всё необходимое для быстрого развертывания на VPS.

Вам понадобится:

`API-ключ из app.exchangerate-api.com`

`BOT-Token вашего ТГ-бота`

## Ручная установка
Если нужно поднять бота локально или развернуть вручную, выполните следующие команды:

````bash
git clone https://github.com/indie-master/exchange_bot.git
cd exchange_bot

# (опционально) создайте виртуальное окружение
python3 -m venv .venv
source .venv/bin/activate

# установите зависимости
pip install -r requirements.txt

# добавьте переменные окружения
echo "BOT_TOKEN=ваш_токен" >> .env
echo "API_KEY=ваш_api_key" >> .env

# запустите бота
python3 exchange_bot.py
````

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
Инсталлятор также регистрирует `systemd`-сервис, который стартует при загрузке
сервера и автоматически перезапускает бота после сбоев процесса.

Для проверки его работы, откройте файл логов:
````
journalctl -u exchange_bot -f
````
Убедитесь, что бот активен и работает корректно.

## Дополнительно
### CLI-менеджер (CBR-rates)
После установки проекта можно управлять ботом через интерактивный CLI.
Менеджер перенаправляет все действия в systemd-сервис `exchange_bot`, поэтому перед
использованием убедитесь, что вы настроили сервис согласно инструкции ниже.

```
cd ~/exchange_bot
./CBR-rates
```

Запуск команды `CBR-rates` без аргументов откроет меню со следующими действиями:

| Команда   | Что делает |
|-----------|------------|
| `status`  | Выполняет `systemctl status exchange_bot --no-pager`. |
| `update`  | Выполняет `git pull --ff-only` для обновления кода. |
| `restart` | Запускает `systemctl restart exchange_bot`. |
| `reload`  | Вызывает `systemctl reload-or-restart exchange_bot` для перечитывания `.env` и кода. |
| `logs`    | Показывает последние строки журнала через `journalctl -u exchange_bot -n 40`. |
| `stop`    | Выполняет `systemctl stop exchange_bot`. |
| `start`   | Выполняет `systemctl start exchange_bot`. |
| `delete`  | Выполняет `systemctl disable --now exchange_bot`, отключая автозапуск. |

Любую команду можно вызвать напрямую, например `./CBR-rates status` или `./CBR-rates restart`.

#### Запуск из любого каталога
Чтобы не заходить в каталог бота каждый раз:

1. Создайте симлинк в директории, которая находится в `$PATH`:
   ```bash
   sudo ln -s /home/bot/exchange_bot/CBR-rates /usr/local/bin/CBR-rates
   ```
2. Если симлинк лежит вне корня репозитория, подскажите CLI путь до него:
   ```bash
   export EXCHANGE_BOT_ROOT=/home/bot/exchange_bot
   ```
3. Теперь `CBR-rates` можно запускать из любого места. Скрипт сам найдёт репозиторий
   (поднимается вверх по текущему каталогу и ищет `bot_cli.py`, а затем использует
   путь из симлинка/переменной).

Для единичного запуска можно сразу передать путь до репозитория флагом `-C/--root`
— он имеет приоритет над переменной окружения:

```bash
CBR-rates -C /home/bot/exchange_bot status
```

### Перезапуск бота
Если нужно перезапустить бота, вызовите unit через CLI или напрямую:
````
./CBR-rates restart
# или
sudo systemctl restart exchange_bot
````

### Остановка бота
Для полной остановки сервиса выполните:
````
./CBR-rates stop
# или
sudo systemctl stop exchange_bot
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
After=network-online.target
Wants=network-online.target

[Service]
User=<ваш_пользователь>
WorkingDirectory=/<ваш_пользователь>/exchange_bot
ExecStart=/<ваш_пользователь>/exchange_bot/venv/bin/python3 exchange_bot.py
Restart=on-failure
RestartSec=5
StartLimitIntervalSec=60
StartLimitBurst=3
StandardOutput=journal
StandardError=journal
EnvironmentFile=/<ваш_пользователь>/exchange_bot/.env

[Install]
WantedBy=multi-user.target
````

Замените `<ваш_пользователь>` на имя вашего пользователя.

### 2. Перезагрузите Systemd и активируйте сервис:

````
sudo systemctl daemon-reload
sudo systemctl enable --now exchange_bot
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

Unit включён для автозапуска после перезагрузки сервера и автоматически
перезапускает процесс при сбоях.

Настройка через Systemd автоматизирует перезапуск и упрощает управление ботом.

## Проблемы и решения
Скрипт выдаёт ошибку "requirements.txt не найден":

Убедитесь, что файл `requirements.txt` добавлен в репозиторий и содержит список всех зависимостей.
Бот не запускается:

Проверьте логи через `journalctl -u exchange_bot` для получения дополнительной информации о проблеме.

Необходимо обновить код бота:

### Выполните следующие команды для обновления:
````
cd ~/exchange_bot
git pull
````
