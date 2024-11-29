#!/bin/bash

# Скрипт для установки и запуска проекта

echo "Начало установки проекта..."

# 1. Убедимся, что система обновлена
echo "Обновление системы..."
sudo apt update && sudo apt upgrade -y

# 2. Установка необходимых пакетов
echo "Установка Python и pip..."
sudo apt install -y python3 python3-pip python3-venv git

# 3. Клонирование репозитория
REPO_URL="https://github.com/indie-master/exchange_bot.git"
INSTALL_DIR="$HOME/exchange_bot"

if [ -d "$INSTALL_DIR" ]; then
    echo "Каталог $INSTALL_DIR уже существует, обновление репозитория..."
    cd "$INSTALL_DIR" && git pull
else
    echo "Клонирование репозитория..."
    git clone "$REPO_URL" "$INSTALL_DIR"
fi

# 4. Настройка виртуального окружения
echo "Настройка виртуального окружения..."
cd "$INSTALL_DIR"
python3 -m venv venv
source venv/bin/activate

# 5. Установка зависимостей
echo "Установка зависимостей из requirements.txt..."
pip install --upgrade pip
pip install -r requirements.txt

# 6. Настройка переменных окружения
echo "Настройка переменных окружения..."
if [ ! -f .env ]; then
    echo "Создание файла .env..."
    cat > .env <<EOL
TOKEN=your_bot_token
DATABASE_URL=sqlite:///database.db
EOL
    echo "Заполните файл .env своими данными!"
else
    echo "Файл .env уже существует."
fi

# 7. Запуск проекта
echo "Запуск проекта..."
nohup python3 bot.py &

echo "Установка завершена! Проект запущен."

