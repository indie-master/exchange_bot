"""Command-line helper that proxies bot actions to the systemd service."""
from __future__ import annotations

import os
import subprocess
import sys
import textwrap
from pathlib import Path
from typing import Callable, Dict, Optional, Tuple

BASE_DIR = Path(__file__).resolve().parent
SERVICE_NAME = "exchange_bot"


def _needs_sudo() -> bool:
    try:
        return os.geteuid() != 0
    except AttributeError:  # pragma: no cover - Windows is not a target platform
        return False


def _sudo_prefix() -> list[str]:
    return ["sudo"] if _needs_sudo() else []


def _systemctl_args(*extra: str) -> list[str]:
    return [*_sudo_prefix(), "systemctl", *extra]


def _journalctl_args(*extra: str) -> list[str]:
    return [*_sudo_prefix(), "journalctl", *extra]


def _run_command(command: list[str], *, capture: bool = True) -> bool:
    if capture:
        result = subprocess.run(command, capture_output=True, text=True)
        stdout = result.stdout.strip()
        stderr = result.stderr.strip()
        if stdout:
            print(stdout)
        if result.returncode != 0 and stderr:
            print(stderr)
    else:
        result = subprocess.run(command)
        if result.returncode != 0:
            joined = " ".join(command)
            print(f"Команда '{joined}' завершилась с кодом {result.returncode}.")
    return result.returncode == 0


def _consume_root_arg(args: list[str]) -> Tuple[Optional[Path], list[str]]:
    """Extract -C/--root if provided, returning the path and remaining args."""

    if not args:
        return None, args

    normalized = []
    root: Optional[Path] = None
    skip_next = False
    for idx, value in enumerate(args):
        if skip_next:
            skip_next = False
            continue
        if value in {"-C", "--root"}:
            if idx + 1 >= len(args):
                print("Флаг -C/--root требует путь после себя.")
                raise SystemExit(1)
            root = Path(args[idx + 1]).expanduser().resolve()
            skip_next = True
            continue
        normalized.append(value)
    return root, normalized


def _find_repo_upwards(start: Path) -> Optional[Path]:
    """Walk up from *start* until bot_cli.py is found or root is reached."""

    current = start.resolve()
    for ancestor in [current, *current.parents]:
        if (ancestor / "bot_cli.py").exists():
            return ancestor
    return None


def _determine_base_dir(explicit: Optional[Path]) -> Path:
    """Return the repository root, honoring overrides and fallbacks."""

    env_root = os.environ.get("EXCHANGE_BOT_ROOT")
    candidates = [explicit, Path(env_root).expanduser().resolve() if env_root else None]
    candidates.append(_find_repo_upwards(Path.cwd()))
    candidates.append(Path(__file__).resolve().parent)

    for candidate in candidates:
        if candidate and (candidate / "bot_cli.py").exists():
            return candidate
    return Path(__file__).resolve().parent


def _set_base_dir(path: Path) -> None:
    global BASE_DIR
    BASE_DIR = path


def status() -> None:
    print("Проверяем состояние systemd-сервиса exchange_bot...")
    _run_command(_systemctl_args("status", SERVICE_NAME, "--no-pager"), capture=False)


def start() -> None:
    print("Запускаем systemd-сервис exchange_bot...")
    if _run_command(_systemctl_args("start", SERVICE_NAME)):
        print("Сервис запущен.")


def stop() -> None:
    print("Останавливаем systemd-сервис exchange_bot...")
    if _run_command(_systemctl_args("stop", SERVICE_NAME)):
        print("Сервис остановлен.")


def restart() -> None:
    print("Перезапускаем systemd-сервис exchange_bot...")
    if _run_command(_systemctl_args("restart", SERVICE_NAME)):
        print("Сервис перезапущен.")


def reload_bot() -> None:
    print("Запускаем reload-or-restart для обмена конфигурацией...")
    if _run_command(_systemctl_args("reload-or-restart", SERVICE_NAME)):
        print("Сервис перечитал конфигурацию (или был перезапущен).")


def show_logs(lines: int = 40) -> None:
    print(f"Показываем последние {lines} строк журнала systemd...")
    _run_command(
        _journalctl_args("-u", SERVICE_NAME, "-n", str(lines), "--no-pager")
    )


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
    print("Останавливаем сервис и отключаем автозапуск exchange_bot...")
    if _run_command(_systemctl_args("disable", "--now", SERVICE_NAME)):
        print(
            "Сервис остановлен и отключён. Удалите файл exchange_bot.service вручную,"
            " если нужно полностью удалить unit."
        )


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
        "status": "Показать вывод systemctl status exchange_bot",
        "update": "Обновить код из git-репозитория",
        "restart": "Выполнить systemctl restart exchange_bot",
        "reload": "Выполнить systemctl reload-or-restart exchange_bot",
        "logs": "Показать journalctl -u exchange_bot",
        "stop": "Выполнить systemctl stop exchange_bot",
        "start": "Выполнить systemctl start exchange_bot",
        "delete": "Выполнить systemctl disable --now exchange_bot",
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
    explicit_root, remaining = _consume_root_arg(args)
    _set_base_dir(_determine_base_dir(explicit_root))

    if not remaining:
        _interactive_loop()
        return

    command = remaining[0].lower()
    if command not in COMMANDS:
        print("Неизвестная команда. Доступные: " + ", ".join(COMMANDS.keys()))
        raise SystemExit(1)

    COMMANDS[command]()


if __name__ == "__main__":
    main()
