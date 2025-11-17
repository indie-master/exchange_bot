#!/bin/bash

echo "=== Установка Exchange Bot ==="

# 1. Проверка и установка необходимых пакетов
echo "Обновляем систему и устанавливаем зависимости..."
sudo apt update && sudo apt install -y python3 python3-pip python3-venv git

# 2. Клонирование репозитория
REPO_URL="https://github.com/indie-master/exchange_bot.git"
INSTALL_DIR="$HOME/exchange_bot"

if [ -d "$INSTALL_DIR" ]; then
    echo "Каталог $INSTALL_DIR уже существует. Удаляем старую версию..."
    rm -rf "$INSTALL_DIR"
fi

echo "Клонируем репозиторий..."
git clone "$REPO_URL" "$INSTALL_DIR"

# 3. Переход в каталог проекта
cd "$INSTALL_DIR" || exit

# 4. Настройка виртуального окружения
echo "Создаем виртуальное окружение..."
python3 -m venv venv
source venv/bin/activate

# 5. Установка зависимостей
echo "Устанавливаем зависимости из requirements.txt..."
pip install --upgrade pip
if [ -f requirements.txt ]; then
    pip install -r requirements.txt
else
    echo "Файл requirements.txt не найден. Убедитесь, что он есть в репозитории."
    exit 1
fi

# 6. Настройка .env файла
ENV_FILE=".env"
if [ ! -f "$ENV_FILE" ]; then
    echo "Создаем .env файл..."
    touch "$ENV_FILE"
else
    echo "Файл .env уже существует."
fi

echo "Пожалуйста, введите API_KEY для вашего бота:"
read -r API_KEY
echo "API_KEY=$API_KEY" > "$ENV_FILE"

echo "Пожалуйста, введите BOT_TOKEN для вашего бота:"
read -r BOT_TOKEN
echo "BOT_TOKEN=$BOT_TOKEN" >> "$ENV_FILE"

echo ".env файл настроен!"

# 7. Создание systemd-сервиса с автозапуском и авто-перезапуском
SERVICE_FILE="/etc/systemd/system/exchange_bot.service"
echo "Создаем systemd unit ${SERVICE_FILE}..."
sudo tee "$SERVICE_FILE" > /dev/null <<EOF
[Unit]
Description=Exchange Bot
After=network-online.target
Wants=network-online.target

[Service]
User=$USER
WorkingDirectory=$INSTALL_DIR
EnvironmentFile=$INSTALL_DIR/.env
ExecStart=$INSTALL_DIR/venv/bin/python3 exchange_bot.py
Restart=on-failure
RestartSec=5
StartLimitIntervalSec=60
StartLimitBurst=3
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

echo "Перезагружаем systemd и включаем автозапуск сервиса..."
sudo systemctl daemon-reload
sudo systemctl enable --now exchange_bot

echo "=== Установка завершена! ==="
echo "Сервис exchange_bot включен, настроен на автозапуск после перезагрузки и автоматический перезапуск при сбоях."

