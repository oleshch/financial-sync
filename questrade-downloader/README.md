## Questrade Downloader

THis cron uses the questrade API to pull and save all the account activities for all active accounts in your questrade account.

### Local Installation

To setup the cron for the first time you have to:
1. Create a python virtual environment called `questrade-downloader-venv` using the following command `virtualenv --python=python3 questrade-downloader-venv`
1. Create local output and logs directories with `mkdir logs`
1. Launch the virtual environment with `source questrade-downloader-venv/bin/activate`
1. Run `pip install -r requirements.txt` to install all the dependencies
1. Create the staging and account tables in your database using the [`create-tables.sql`](./create-tables.sql) query
1. [Generate](https://login.questrade.com/APIAccess/UserApps.aspx) a manual refresh token and save it in your [`config.json`](./config-sample.json) file
1. Run the script using `python questrade-downloader.py`

### Crontab Command
```
~/financial-sync/questrade-downloader/questrade-downloader-venv/bin/python ~/financial-sync/questrade-downloader/questrade-downloader.py >~/financial-sync/questrade-downloader/logs/LOG.log 2>~/financial-sync/questrade-downloader/logs/ERROR.err ; { if [ -s ~/financial-sync/questrade-downloader/logs/ERROR.err ]; then cat ~/financial-sync/questrade-downloader/logs/ERROR.err ; fi; } | ~/financial-sync/pushbullet-notifications/pushbullet-notifications-venv/bin/python ~/analytics_crons/pushbullet-notifications/pushbullet-notifications.py
```