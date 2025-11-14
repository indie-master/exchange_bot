# CBR-rates-bot (formerly Exchange Bot)
CBR-rates-bot is a Telegram bot for automating currency conversions using the official rates of the Central Bank of Russia with the ability to pick a publication date.
This project includes everything you need for fast deployment on a VPS.

## Features

- Pulls the official USD, EUR and CNY rates from the Central Bank of Russia for any date selected by the user.
- Converts in every supported direction (RUB↔USD, RUB↔EUR, RUB↔CNY as well as USD↔EUR, USD↔CNY and EUR↔CNY).
- Provides a structured inline menu (forward/back buttons and a persistent reply keyboard) so you do not have to type `/start` every time you want to return to the main screen.

### Using the bot

1. Tap **🏠 Menu** on the reply keyboard (or press `/start` the first time) to open the main dashboard with current rates.
2. Pick **💱 Conversion** and select the base currency, then the target currency. After that enter the amount and the bot will display the result along with the official publication date.
3. Press **📅 Choose date** to enter a date in `DD.MM.YYYY` format and reload the rates for that day.

The inline menu always contains “Back” buttons so you can jump between sub-menus without leaving the chat.

You will need:

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
curl -O https://raw.githubusercontent.com/indie-master/CBR-rates-bot/main/setup_cbr_rates_bot.sh
````

### Making the script executable
````
chmod +x setup_cbr_rates_bot.sh
````

### Running the script
````
./setup_cbr_rates_bot.sh
````

### Step 3: Configuration
During the execution of the script, you will be asked to enter `BOT_TOKEN` — the token of your Telegram bot.
It will be automatically saved to the `.env` file.

### Step 4: Launch
After the script is completed, the bot will start automatically.

To check its operation, open the log file:
````
tail -f bot.log
````
Make sure that the bot is active and working correctly.

## Additional
### Publishing the renamed CBR-rates-bot repository
If you cloned the previous `exchange_bot` repo and now want to rebrand and push it as
`CBR-rates-bot`, follow these steps:

1. Rename the project directory so it matches the new bot name:
   ```
   mv exchange_bot CBR-rates-bot
   cd CBR-rates-bot
   ```
2. Clean up the old Git remote and point the repo to the new GitHub project (create
   an empty `CBR-rates-bot` repo beforehand):
   ```
   git remote remove origin
   git remote add origin git@github.com:<your-user>/CBR-rates-bot.git
   ```
3. Commit the rename (this README, the setup script, service files, etc. already use
   the new branding) and push the current branch:
   ```
   git add -A
   git commit -m "Rename project to CBR-rates-bot"
   git push -u origin main
   ```
4. Re-run the installation script from the new repository URL (see the commands
   above) so every fresh deployment pulls from `CBR-rates-bot`.

These steps keep your Git history intact while moving development to the renamed
repository.

### Resolving dependency conflicts
If `pip install -r requirements.txt` fails with a message similar to
```
ERROR: Cannot install -r requirements.txt (line 10) and httpx==0.28.1 because these package versions have conflicting dependencies
```
you most likely have an old virtual environment (or an older copy of the
repository) where `httpx==0.28.1` was pinned manually. The current bot relies
on `python-telegram-bot==20.8`, which already pulls the compatible
`httpx~=0.26.0`, so you only need to remove the stale pin and reinstall.

1. Update the repository and remove the previous virtual environment:
   ```
   cd ~/CBR-rates-bot
   git pull
   rm -rf venv
   ```
2. Re-create the environment and install the trimmed dependency set:
   ```
   python3 -m venv venv
   source venv/bin/activate
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

These steps ensure that `pip` no longer attempts to install an incompatible
`httpx` version and that the bot uses the tested dependency versions.

### Restart the bot
If you need to restart the bot, run the following commands:
````
cd ~/CBR-rates-bot
source venv/bin/activate`
nohup python3 exchange_bot.py > bot.log 2>&1 &
````

### Stopping the bot
To stop the process, find its ID and complete:
````
ps aux | grep exchange_bot.py
kill <PROCESS_ID>
````

## CLI management with `CBR-rates`

You can manage the bot without remembering long `systemctl` commands by using
the included `CBR-rates` helper script.

1. Copy the script to a directory in your `$PATH` (or create a symlink):
   ```
   sudo ln -s ~/CBR-rates-bot/CBR-rates /usr/local/bin/CBR-rates
   ```
2. Make sure it is executable:
   ```
   chmod +x ~/CBR-rates-bot/CBR-rates
   ```
3. Type `CBR-rates` in the terminal. The script shows an interactive menu with
   the following actions:

   | Option  | Description |
   |---------|-------------|
   | Status  | `systemctl status cbr_rates_bot.service` without paging |
   | Update  | `git fetch && git pull --rebase` inside `~/CBR-rates-bot` |
   | Restart | `systemctl restart cbr_rates_bot.service` |
   | Reload  | Runs `systemctl daemon-reload` and then `systemctl reload`
   (falls back to restart) |
   | Logs    | Follows the last 100 lines of
   `journalctl -u cbr_rates_bot.service` |
   | Stop    | Stops the service |
   | Start   | Starts the service |
   | Delete  | Stops/disables the service, removes the unit file and deletes
   the `~/CBR-rates-bot` directory (asks for confirmation) |

The helper assumes you installed the bot to `~/CBR-rates-bot` and created a
systemd unit named `cbr_rates_bot.service`. Adjust the `SERVICE_NAME` and
`REPO_DIR` variables at the top of the script if your environment differs.

## Setup via Systemd
### 1. Create a service file:
Open the editor and create a new file:

````
sudo nano /etc/systemd/system/cbr_rates_bot.service
````

Add the following configuration:
````
[Unit]
Description=CBR-rates-bot
After=network.target

[Service]
User=<your_user>
WorkingDirectory=/<your_user>/CBR-rates-bot
ExecStart=/<your_user>/CBR-rates-bot/venv/bin/python3 exchange_bot.py
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal
EnvironmentFile=/<your_user>/CBR-rates-bot/.env

[Install]
WantedBy=multi-user.target
````

Replace `<your_user>` with your username.

### 2. Restart Systemd and activate the service:

````
sudo systemctl daemon-reload
sudo systemctl enable cbr_rates_bot
````

### 3. Launch the bot:

````
sudo systemctl start cbr_rates_bot
````

### 4. Restart after changes:
After changing the token or code, restart the service:

````
sudo systemctl restart cbr_rates_bot
````

### 5. Checking the status:
Make sure that the bot is working:

````
sudo systemctl status cbr_rates_bot
````

Setting up via Systemd automates restarts and simplifies bot management.
