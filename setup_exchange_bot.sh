#!/bin/bash

echo "Начинаем установку бота Exchange Bot на вашем сервере VPS..."

# Шаг 1: Установить необходимые зависимости
echo "Устанавливаем зависимости..."
sudo apt update
sudo apt install -y python3 python3-venv python3-pip git

# Шаг 2: Клонирование проекта с GitHub
read -p "Введите URL репозитория вашего бота (например, https://github.com/username/exchange-bot): " REPO_URL

if [[ -n "$REPO_URL" ]]; then
  echo "Клонируем проект с GitHub..."
  git clone "$REPO_URL" exchange_bot || { echo "Не удалось клонировать репозиторий"; exit 1; }
  cd exchange_bot
else
  echo "Вы выбрали использовать текущую директорию. Убедитесь, что здесь находится проект бота."
fi

# Шаг 3: Создаем виртуальное окружение
echo "Создаем виртуальное окружение..."
python3 -m venv venv
source venv/bin/activate

# Шаг 4: Установка зависимостей
echo "Устанавливаем Python-зависимости..."
pip install -r requirements.txt

# Шаг 5: Ввод переменных окружения
if [[ ! -f .env ]]; then
  echo "Введите ключи для настройки бота:"
  read -p "Введите API_KEY от app.exchangerate-api.com: " API_KEY
  read -p "Введите BOT_TOKEN: " BOT_TOKEN

  echo "Создаем .env файл..."
  cat <<EOL >.env
API_KEY=$API_KEY
BOT_TOKEN=$BOT_TOKEN
EOL
fi

# Шаг 6: Настройка systemd для автозапуска
SERVICE_NAME="exchange_bot"
echo "Создаем сервис systemd для автозапуска бота..."
cat <<EOL | sudo tee /etc/systemd/system/$SERVICE_NAME.service
[Unit]
Description=Exchange Bot Telegram
After=network.target

[Service]
User=$USER
WorkingDirectory=$(pwd)
ExecStart=$(pwd)/venv/bin/python $(pwd)/exchange_bot.py
Restart=always

[Install]
WantedBy=multi-user.target
EOL

# Шаг 7: Перезагрузка systemd и запуск бота
echo "Перезагружаем systemd и запускаем бота..."
sudo systemctl daemon-reload
sudo systemctl enable $SERVICE_NAME
sudo systemctl start $SERVICE_NAME

# Финальное сообщение
echo "Установка завершена! Бот настроен и запущен."
echo "Для проверки статуса бота используйте команду: sudo systemctl status $SERVICE_NAME"
