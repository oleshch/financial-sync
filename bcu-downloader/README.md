## BCU Downloader

This cron logs into your BCU accounts and downloads your transaction history in CSV format.

### Local Installation

To setup the cron for the first time you have to:
1. Create a python virtual environment called `bcu-downloader-venv` using the following command `virtualenv --python=python3 bcu-downloader-venv`
1. Create local output and logs directories with `mkdir {logs, csvs}`
1. Launch the virtual environment with `source bcu-downloader-venv/bin/activate`
1. Run `pip install -r requirements.txt` to install all the dependencies
1. Create the staging and account tables in your database using the [`create-tables.sql`](./create-tables.sql) query
1. Create the view in your database using the [`create-view.sql`](./create-view.sql) query
1. Fill in the required fields in the  [`config-sample.json`](./config-sample.json) file and save it as `config.json`
1. Run the script using `python bcu-downloader.py`


### Crontab Command
```
~/financial-sync/bcu-downloader/bcu-downloader-venv/bin/python ~/financial-sync/bcu-downloader/bcu-downloader.py >~/financial-sync/bcu-downloader/LOG.log 2>~/financial-sync/bcu-downloader/logs/ERROR.err ; { if [ -s ~/financial-sync/bcu-downloader/logs/ERROR.err ]; then cat ~/financial-sync/bcu-downloader/logs/ERROR.err ; fi; } | ~/financial-sync/pushbullet-notifications/pushbullet-notification-venv/bin/python ~/analytics_crons/pushbullet-notifications/pushbullet-notification.py
```