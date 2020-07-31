## TD Easyweb Visa Downloader

This cron logs into your TD Easyweb accounts and downloads your Visa transaction history in CSV format.

### Local Installation

To setup the cron for the first time you have to:
1. Create a python virtual environment called `td-downloader-venv` using the following command `virtualenv --python=python3 td-downloader-venv`
1. Create local output and logs directories with `mkdir csvs, logs`
1. Launch the virtual environment with `source td-downloader-venv/bin/activate`
1. Run `pip install -r requirements.txt` to install all the dependencies
1. Create the staging and account tables in your database using the [`create-tables.sql`](./create-tables.sql) query
1. Fill in the required fields in the  [`config-sample.json`](./config-sample.json) file and save it as `config.json`
1. Run the script using `python td-downloader.py`

### Crontab Command
```
~/financial-sync/td-downloader/td-downloader-venv/bin/python ~/financial-sync/td-downloader/td-downloader.py >~/financial-sync/td-downloader/logs/LOG.log 2>~/financial-sync/td-downloader/logs/ERROR.err ; { if [ -s ~/financial-sync/td-downloader/logs/ERROR.err ]; then cat ~/financial-sync/td-downloader/logs/ERROR.err ; fi; } | ~/financial-sync/pushbullet-notifications/pushbullet-notifications-venv/bin/python ~/financial-sync/pushbullet-notifications/pushbullet-notifications.py
```