#!/bin/bash

# Скрипт установки и запуска проекта

echo "=== Начало установки проекта ==="

# 1. Обновление системы
echo "Обновляем список пакетов..."
sudo apt update && sudo apt upgrade -y

# 2. Установка необходимых пакетов
echo "Устанавливаем Python, pip, и git..."
sudo apt install -y python3 python3-pip python3-venv git

# 3. Клонирование репозитория
REPO_URL="https://github.com/indie-master/exchange_bot.git"
INSTALL_DIR="$HOME/exchange_bot"

if [ -d "$INSTALL_DIR" ]; then
    echo "Каталог $INSTALL_DIR уже существует. Обновляем репозиторий..."
    cd "$INSTALL_DIR" && git pull
else
    echo "Клонируем репозиторий..."
    git clone "$REPO_URL" "$INSTALL_DIR"
fi

# Переход в каталог проекта
cd "$INSTALL_DIR"

# 4. Настройка виртуального окружения
echo "Создаем и активируем виртуальное окружение..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate

# 5. Установка зависимостей
echo "Устанавливаем зависимости из requirements.txt..."
pip install --upgrade pip
if [ -f requirements.txt ]; then
    pip install -r requirements.txt
else
    echo "Файл requirements.txt не найден! Убедитесь, что он есть в репозитории."
    exit 1
fi

# 6. Настройка переменных окружения
echo "Проверяем файл .env..."
if [ ! -f .env ]; then
    echo "Файл .env отсутствует. Создаем шаблон..."
    cat > .env <<EOL
# Замените эти значения своими
TOKEN=your_bot_token
DATABASE_URL=sqlite:///database.db
EOL
    echo "Файл .env создан. Пожалуйста, отредактируйте его перед запуском!"
else
    echo "Файл .env уже существует."
fi

# 7. Проверка структуры проекта
MAIN_SCRIPT="exchange_bot.py" # Замените на имя вашего основного файла
if [ ! -f "$MAIN_SCRIPT" ]; then
    echo "Файл $MAIN_SCRIPT не найден! Укажите правильное название основного файла."
    echo "Или вручную отредактируйте переменную MAIN_SCRIPT в этом скрипте."
    exit 1
fi

# 8. Запуск проекта
echo "Запускаем проект..."
nohup python3 "$MAIN_SCRIPT" > bot.log 2>&1 &

echo "=== Установка завершена! ==="
echo "Бот запущен в фоновом режиме. Логи записываются в bot.log."
