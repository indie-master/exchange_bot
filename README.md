# Exchange Bot
Exchange Bot is a telegram bot for automating the calculation of currency exchange at current exchange rates based on data from the source app.exchangerate-api.com .
This project includes everything you need for fast deployment on a VPS.

You will need:

`API key from app.exchangerate-api.com `

`BOT Token of your TG bot`

## Installation and launch
Follow the steps below to install and run the bot on your server.

### Step 1: Preparation
Make sure that your server meets the following requirements:

**Operating system:** `Linux (Ubuntu/Debian)`

**Python:** `3.8 or higher`

**Internet access**

**Installed packages:** `git, python3-pip`

If any of this is not installed, the script will do it for you.

### Step 2: Download and Install
1. Log in to your server's terminal.
2. Copy and execute the following set of commands:
### Download the installation script
````
curl -O https://raw.githubusercontent.com/indie-master/exchange_bot/main/setup_exchange_bot.sh
````

### Making the script executable
````
chmod +x setup_exchange_bot.sh
````

### Running the script
````
./setup_exchange_bot.sh
````

### Step 3: Configuration
During the execution of the script, you will be asked to enter two parameters:

`API_KEY` is the key for connecting to the Telegram API.

`BOT_TOKEN` is the token of your Telegram bot.

This data will be automatically saved to the `.env` file

### Step 4: Launch
After the script is completed, the bot will start automatically.
The installer also registers a `systemd` service that starts on boot and restarts
the bot if the process exits unexpectedly.

To check its operation, open the log file:
````
journalctl -u exchange_bot -f
````
Make sure that the bot is active and working correctly.

## Additional
### CLI manager (CBR-rates)
After cloning or installing the project you can manage the bot through the interactive CLI helper.
The helper proxies every action to the `exchange_bot` systemd service, so make sure you have
completed the service setup from the section below before using these commands.

```
cd ~/exchange_bot
./CBR-rates
```

Running the `CBR-rates` command without arguments opens a menu with the following actions:

| Command  | Description |
|----------|-------------|
| `status` | Runs `systemctl status exchange_bot --no-pager`. |
| `update` | Fetch the latest changes from the git repository (`git pull --ff-only`). |
| `restart`| Executes `systemctl restart exchange_bot`. |
| `reload` | Calls `systemctl reload-or-restart exchange_bot` to re-read `.env` and code. |
| `logs`   | Shows the latest journal lines via `journalctl -u exchange_bot -n 40`. |
| `stop`   | Executes `systemctl stop exchange_bot`. |
| `start`  | Executes `systemctl start exchange_bot`. |
| `delete` | Runs `systemctl disable --now exchange_bot` to stop and disable autostart. |

You can also run a single command directly, for example `./CBR-rates status` or `./CBR-rates restart`.

#### Run from any directory
If you prefer not to `cd` into the repo every time:

1. Create a symlink somewhere on your `$PATH`:
   ```bash
   sudo ln -s /home/bot/exchange_bot/CBR-rates /usr/local/bin/CBR-rates
   ```
2. When the symlink lives outside the repository, point the CLI to the repo root:
   ```bash
   export EXCHANGE_BOT_ROOT=/home/bot/exchange_bot
   ```
3. Now `CBR-rates` can be invoked from anywhere. The helper will climb up from the
   current directory to find `bot_cli.py`, then fall back to the resolved symlink path
   or the `EXCHANGE_BOT_ROOT` hint.

For a one-off call you can pass the path explicitly with `-C/--root` (it overrides
the environment variable):

```bash
CBR-rates -C /home/bot/exchange_bot status
```

### Restart the bot
If you need to restart the bot, trigger the systemd unit (directly or via the CLI helper):
````
./CBR-rates restart
# or
sudo systemctl restart exchange_bot
````

### Stopping the bot
To stop the service entirely, run:
````
./CBR-rates stop
# or
sudo systemctl stop exchange_bot
````

## Setup via Systemd
### 1. Create a service file:
Open the editor and create a new file:

````
sudo nano /etc/systemd/system/exchange_bot.service
````

Add the following configuration:
````
[Unit]
Description=Exchange Bot
After=network-online.target
Wants=network-online.target

[Service]
User=<your_user>
WorkingDirectory=/<your_user>/exchange_bot
ExecStart=/<your_user>/exchange_bot/venv/bin/python3 exchange_bot.py
Restart=on-failure
RestartSec=5
StartLimitIntervalSec=60
StartLimitBurst=3
StandardOutput=journal
StandardError=journal
EnvironmentFile=/<your_user>/exchange_bot/.env

[Install]
WantedBy=multi-user.target
````

Replace `<your_user>` with your username.

### 2. Restart Systemd and activate the service:

````
sudo systemctl daemon-reload
sudo systemctl enable --now exchange_bot
````

### 3. Launch the bot:

````
sudo systemctl start exchange_bot
````

### 4. Restart after changes:
After changing the token or code, restart the service:

````
sudo systemctl restart exchange_bot
````

### 5. Checking the status:
Make sure that the bot is working:

````
sudo systemctl status exchange_bot
````

The unit is enabled for startup after server reboots and will automatically
restart if the process crashes.

Setting up via Systemd automates restarts and simplifies bot management.

## Troubleshooting
The script prints `requirements.txt not found`:

Make sure that `requirements.txt` exists in the repository and lists all dependencies.

The bot does not start:

Check the logs via `journalctl -u exchange_bot` for additional diagnostic information.

You need to update the bot code:

Run the following commands to fetch the latest version:

````
cd ~/exchange_bot
git pull
````
