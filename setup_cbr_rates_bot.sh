#!/bin/bash

echo "=== Установка CBR-rates-bot ==="

# 1. Проверка и установка необходимых пакетов
echo "Обновляем систему и устанавливаем зависимости..."
sudo apt update && sudo apt install -y python3 python3-pip python3-venv git

# 2. Клонирование репозитория
REPO_URL="https://github.com/indie-master/CBR-rates-bot.git"
INSTALL_DIR="$HOME/CBR-rates-bot"

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

# 7. Запуск бота
echo "Запускаем бота..."
nohup python3 exchange_bot.py > bot.log 2>&1 &

echo "=== Установка завершена! ==="
echo "Бот запущен в фоновом режиме. Логи записываются в bot.log."

