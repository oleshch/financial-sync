## Pushbullet Notifications

This script is used to pass error messages from cronjobs to the [Pushbullet](https://www.pushbullet.com/) Notification service

### Local Installation

To setup the cron for the first time you have to:
1. Create a python virtual environment called `pushbullet-notifications-venv` using the following command `virtualenv --python=python3 pushbullet-notifications-venv`
1. Launch the virtual environment with `source pushbullet-notifications-venv/bin/activate`
1. Run `pip install -r requirements.txt` to install all the dependencies
1. Generate a new API key from Pushbullet on the [My Account](https://www.pushbullet.com/#settings/account) page by clicking the Create Access Token button.
1. Fill in the api_key field in the  [`config-sample.json`](./config-sample.json) file and save it as `config.json`.
1. Use the script py piping any error code message to `python pushbullet-notifications.py`

**Acknowledgements**
---

+ Using [@rbrcsk](https://github.com/rbrcsk) [Pushbullet](https://github.com/rbrcsk/pushbullet.py) API wrapper
