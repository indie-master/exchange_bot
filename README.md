<p align="center">
  <img src="docs/logo.svg" alt="Exchange Bot logo" width="120" />
</p>

<p align="center">
  <b>Exchange Bot</b>
</p>

<p align="center">
  <a href="README.md">🇬🇧 English</a> |
  <a href="README.ru.md">🇷🇺 Русский</a>
</p>

Exchange Bot is a Telegram assistant that shows fresh currency rates and manages a systemd-backed bot service. The `CBR-rates` CLI controls the service from any directory once installed.

## Requirements

- Linux host with `python3` and `git`
- Network access to fetch dependencies and currency data
- Permission to create `/usr/local/bin/CBR-rates` (run installer with sudo if needed)

## Quick install (one liner)

Clone + install + symlink in one command:

```bash
bash <(curl -fsSL https://raw.githubusercontent.com/<OWNER>/exchange_bot/main/install.sh)
```

Replace `<OWNER>` with the GitHub owner if your remote differs. The installer will:
- create/activate a virtual environment under the repo
- install Python dependencies
- make `CBR-rates` executable
- link it into `/usr/local/bin` so it works from any directory

## Manual install

```bash
git clone https://github.com/<OWNER>/exchange_bot.git
cd exchange_bot
./install.sh
```

After either path you can immediately run:

```bash
CBR-rates status
```

## Usage

`CBR-rates` talks directly to the `exchange_bot` systemd unit.

```bash
CBR-rates               # interactive menu
CBR-rates status        # systemctl status exchange_bot
CBR-rates restart       # systemctl restart exchange_bot
CBR-rates logs          # journalctl -u exchange_bot -n 40
CBR-rates -C /path status   # override repo root for a one-off call
```

Root resolution order: `-C/--root` flag → `EXCHANGE_BOT_ROOT` env → symlink/CLI location → current directory. No manual `chmod` or symlink creation is required beyond running `install.sh`.

## Configuration

- Place your bot tokens and API keys in the existing `.env` file if required by the bot.
- Optional: set `EXCHANGE_BOT_ROOT=/absolute/path/to/exchange_bot` in your shell profile to pin the repo location.

## Troubleshooting

- **`CBR-rates` not found**: ensure `/usr/local/bin` is in your `PATH` or rerun `./install.sh` with sudo so it can create the symlink.
- **Python import errors**: rerun `./install.sh` to recreate the virtualenv and dependencies.
- **Permission denied on systemctl**: use `sudo CBR-rates <command>` if your user cannot control the service.
