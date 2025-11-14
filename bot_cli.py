"""Command-line helper for managing the exchange bot lifecycle."""
from __future__ import annotations

import os
import signal
import subprocess
import sys
import textwrap
import time
from pathlib import Path
from typing import Callable, Dict, Optional

BASE_DIR = Path(__file__).resolve().parent
BOT_SCRIPT = BASE_DIR / "exchange_bot.py"
LOG_FILE = BASE_DIR / "bot.log"
PID_FILE = BASE_DIR / "bot.pid"


def _read_pid() -> Optional[int]:
    try:
        value = int(PID_FILE.read_text().strip())
    except (FileNotFoundError, ValueError):
        return None
    return value or None


def _is_process_running(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    else:
        return True


def _running_pid() -> Optional[int]:
    pid = _read_pid()
    if pid is None:
        return None
    if _is_process_running(pid):
        return pid
    PID_FILE.unlink(missing_ok=True)
    return None


def _ensure_bot_script() -> None:
    if not BOT_SCRIPT.exists():
        raise FileNotFoundError(
            "exchange_bot.py не найден. Запустите команды из корня репозитория."
        )


def status() -> None:
    pid = _running_pid()
    if pid:
        print(f"Бот запущен (PID {pid}). Логи: {LOG_FILE}")
    else:
        print("Бот не запущен.")


def start() -> None:
    if _running_pid():
        print("Бот уже работает. Используйте restart, чтобы перезапустить.")
        return

    _ensure_bot_script()
    LOG_FILE.touch(exist_ok=True)
    log_handle = LOG_FILE.open("ab", buffering=0)
    process = subprocess.Popen(  # noqa: S603, S607
        [sys.executable, str(BOT_SCRIPT)],
        stdout=log_handle,
        stderr=log_handle,
        cwd=str(BASE_DIR),
        start_new_session=True,
    )
    log_handle.close()
    PID_FILE.write_text(str(process.pid))
    print(f"Бот запущен (PID {process.pid}). Логи: {LOG_FILE}")


def _stop_process(pid: int) -> None:
    os.kill(pid, signal.SIGTERM)
    for _ in range(30):
        if not _is_process_running(pid):
            break
        time.sleep(0.2)
    else:
        print("Процесс не завершился, отправляем SIGKILL...")
        os.kill(pid, signal.SIGKILL)


def stop() -> None:
    pid = _running_pid()
    if not pid:
        print("Бот не запущен.")
        PID_FILE.unlink(missing_ok=True)
        return

    _stop_process(pid)
    PID_FILE.unlink(missing_ok=True)
    print("Бот остановлен.")


def restart() -> None:
    print("Перезапуск бота...")
    stop()
    start()


def reload_bot() -> None:
    pid = _running_pid()
    if not pid:
        print("Бот не запущен, reload невозможен. Используйте start.")
        return

    print("Reload выполняет мягкий перезапуск для перечитывания .env и кода.")
    _stop_process(pid)
    start()


def show_logs(lines: int = 40) -> None:
    if not LOG_FILE.exists():
        print("Файл логов ещё не создан.")
        return

    print(f"Последние {lines} строк {LOG_FILE}:")
    with LOG_FILE.open("r", encoding="utf-8", errors="ignore") as fh:
        content = fh.readlines()
    for line in content[-lines:]:
        print(line.rstrip())


def update_repo() -> None:
    print("Обновляем репозиторий из удалённого...")
    result = subprocess.run(  # noqa: S603, S607
        ["git", "pull", "--ff-only"],
        cwd=str(BASE_DIR),
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        print(result.stdout.strip() or "Репозиторий уже обновлён.")
    else:
        print("Не удалось обновить репозиторий:")
        print(result.stderr.strip())


def delete() -> None:
    print("Удаляем запущенный бот и сервисные файлы (bot.log, bot.pid)...")
    stop()
    for file in (LOG_FILE, PID_FILE):
        try:
            file.unlink()
        except FileNotFoundError:
            continue
    print("Удаление завершено. Репозиторий остаётся без изменений.")


COMMANDS: Dict[str, Callable[[], None]] = {
    "status": status,
    "update": update_repo,
    "restart": restart,
    "reload": reload_bot,
    "logs": show_logs,
    "stop": stop,
    "start": start,
    "delete": delete,
}


def _print_menu() -> None:
    descriptions = {
        "status": "Показать состояние фонового процесса бота",
        "update": "Обновить код из git-репозитория",
        "restart": "Остановить и снова запустить бота",
        "reload": "Перезапустить для перечитывания конфигурации",
        "logs": "Показать последние строки логов",
        "stop": "Остановить бота",
        "start": "Запустить бота",
        "delete": "Удалить PID/лог и остановить бота",
    }

    print(
        textwrap.dedent(
            """
            === CBR Rates Manager ===
            Доступные команды:
            """
        ).strip()
    )
    for idx, name in enumerate(COMMANDS, start=1):
        print(f"  {idx}. {name:<7} — {descriptions[name]}")
    print("  q. Выход")


def _interactive_loop() -> None:
    while True:
        _print_menu()
        choice = input("Введите команду или номер: ").strip().lower()
        if choice in {"q", "quit", "exit"}:
            print("Выход из менеджера.")
            break
        if choice.isdigit():
            index = int(choice) - 1
            if 0 <= index < len(COMMANDS):
                command = list(COMMANDS.values())[index]
                command()
                continue
        if choice in COMMANDS:
            COMMANDS[choice]()
            continue
        print("Неизвестная команда. Попробуйте снова.")


def main(argv: Optional[list[str]] = None) -> None:
    args = list(sys.argv[1:] if argv is None else argv)
    if not args:
        _interactive_loop()
        return

    command = args[0].lower()
    if command not in COMMANDS:
        print("Неизвестная команда. Доступные: " + ", ".join(COMMANDS.keys()))
        raise SystemExit(1)

    COMMANDS[command]()


if __name__ == "__main__":
    main()
