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

`API_KEY' is the key for connecting to the Telegram API.

`BOT_TOKEN' is the token of your Telegram bot.

This data will be automatically saved to the '.env` file

### Step 4: Launch
After the script is completed, the bot will start automatically.

To check its operation, open the log file:
````
tail -f bot.log
````
Make sure that the bot is active and working correctly.

## Additional
### CLI manager (CBR-rates)
After cloning or installing the project you can manage the bot through the interactive CLI helper:

```
cd ~/exchange_bot
./CBR-rates
```

Running the `CBR-rates` command without arguments opens a menu with the following actions:

| Command  | Description |
|----------|-------------|
| `status` | Show whether the background bot process is running and display the log path. |
| `update` | Fetch the latest changes from the git repository (`git pull --ff-only`). |
| `restart`| Stop and start the bot again. |
| `reload` | Graceful restart that re-reads `.env` and the Python code. |
| `logs`   | Print the last lines of `bot.log`. |
| `stop`   | Terminate the background bot process. |
| `start`  | Start the bot if it is not running. |
| `delete` | Stop the bot and remove helper files (`bot.log`, `bot.pid`). |

You can also run a single command directly, for example `./CBR-rates status` or `./CBR-rates restart`.

### Restart the bot
If you need to restart the bot, run the following commands:
````
cd ~/exchange_bot
source venv/bin/activate`
nohup python3 exchange_bot.py > bot.log 2>&1 &
````

### Stopping the bot
To stop the process, find its ID and complete:
````
ps aux | grep exchange_bot.py
kill <PROCESS_ID>
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
After=network.target

[Service]
User=<your_user>
WorkingDirectory=/<your_user>/exchange_bot
ExecStart=/<your_user>/exchange_bot/venv/bin/python3 exchange_bot.py
Restart=always
RestartSec=5
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
sudo systemctl enable exchange_bot
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

Setting up via Systemd automates restarts and simplifies bot management.
