#!/usr/bin/env python3

import os
import sys
import json
import pytz
import pprint
import logging
import psycopg2
from datetime import datetime, timedelta
from dateutil.rrule import rrule, MONTHLY
from dateutil.relativedelta import relativedelta
from questrade_api import Questrade

# Setting up the logging to send ERRORS to STDERR
# Set logging.ERROR to logging.INFO to enable all logging
logger = logging.getLogger()
if sys.platform  == "darwin" or sys.platform == "win32":
  logger.setLevel(logging.INFO)
else:
  logger.setLevel(logging.ERROR)

# Read Config File
script_path=os.path.dirname(os.path.realpath(__file__))
base_folder=os.path.dirname(script_path)
file_path =  os.path.join(script_path, 'config.json')
db_file_path =  os.path.join(base_folder, 'db-config.json')
home_path = os.path.expanduser('~')

# Database fields
with open(db_file_path) as file:
  config = json.load(file)
  db_user = config["db_user"]
  db_password = config["db_password"]
  db_host = config["db_host"]
  db_port = config["db_port"]
  db_database = config["db_database"]

# Questrade Secrets
with open(file_path) as file:
  config = json.load(file)
  refresh_token = config["refresh_token"]

tz = pytz.utc
now = datetime.utcnow().astimezone(tz)

# Connect to Database
connection = psycopg2.connect(user = db_user,
                              password = db_password,
                              host = db_host,
                              port = db_port,
                              database = db_database)

cursor = connection.cursor()
logging.info(f"Connecting to database {db_database}")

# Connect to Questrade
if os.path.exists(home_path + '/.questrade.json'):
  try:
    q = Questrade()
  except Exception as e:
    logging.error(e)
    with open(home_path + '/.questrade.json') as file:
      config = json.load(file)
      q_refresh_token = config["refresh_token"]
      q = Questrade(refresh_token=q_refresh_token)
else:
  q = Questrade(refresh_token=refresh_token)

# Returns a list of Start and End dates from start_date to now()
def month_iter(start_date):
  todays_date = now
  month_list = []
  for month_date in rrule(MONTHLY, dtstart=start_date, until=todays_date):
    end_of_month = month_date + relativedelta(day=31)
    if end_of_month >= todays_date:
      end_of_month = todays_date
    month_list.append((month_date.isoformat(), end_of_month.isoformat()))
  return month_list


def get_insert_activities(month):
  start_date = month[0]
  end_date = month[1]

  try:
    account_month_info = q.account_activities(account_id, startTime=start_date, endTime=end_date)
  except Exception as e:
    return e

  if account_month_info.get("activities") == None:
    logger.error(f"Error: {account_month_info}")
    return

  for activity in account_month_info["activities"]:

    description = activity["description"].replace("'","''")

    insert_query = f"""INSERT INTO staging.{table} (action, commission, currency, description, grossAmount, netAmount, price, quantity, settlementDate, symbol, symbolId, tradeDate, transactionDate, type) VALUES
    (
      '{activity["action"]}',
      {activity["commission"]},
      '{activity["currency"]}',
      '{description}',
      {activity["grossAmount"]},
      {activity["netAmount"]},
      {activity["price"]},
      {activity["quantity"]},
      '{activity["settlementDate"]}',
      '{activity["symbol"]}',
      {activity["symbolId"]},
      '{activity["tradeDate"]}',
      '{activity["transactionDate"]}',
      '{activity["type"]}'
    );"""
    cursor.execute(insert_query)

  #Insert Sync Row
  cursor.execute(f"INSERT INTO staging.sync_log (account, last_sync_date) VALUES ('{table}','{end_date}');")

  connection.commit()

def insert_from_staging(table):

  insert_query = f"""INSERT INTO accounts.{table}
  (action, commission, currency, description, grossAmount, netAmount, price, quantity, settlementDate, symbol, symbolId, tradeDate, transactionDate, type)
  SELECT DISTINCT
    action,
    commission,
    currency,
    trim(regexp_replace(description, '\s+', ' ', 'g')),
    grossAmount,
    netAmount,
    price,
    quantity,
    settlementDate::TIMESTAMPTZ,
    symbol,
    symbolId,
    tradeDate::TIMESTAMPTZ,
    transactionDate::TIMESTAMPTZ,
    type
  FROM staging.{table}
  WHERE action || commission || currency || description || grossAmount || netAmount || price || quantity || settlementDate || symbol || symbolId || tradeDate || transactionDate || type
 NOT IN (SELECT
    action || commission || currency || description || grossAmount || netAmount || price || quantity || settlementDate || symbol || symbolId || tradeDate || transactionDate || type
  FROM accounts.{table});
  """
  cursor.execute(insert_query)
  connection.commit()
  logging.info(f"Loaded {table} from staging")

###################################
######## Start Main Script ########
###################################

# Get account information from Questrade

try:
  accounts = q.accounts
  accounts.get("accounts")
except Exception as e:
  logger.error(f"Error: {e}")
finally:
  if accounts.get("accounts") == None:
    logger.error(f"Error: {accounts}")
    sys.exit(1)


# For each Account
for account in accounts["accounts"]:
  table = 'questrade_' + account["type"].lower()
  account_name = account["clientAccountType"] + ' ' + account["type"]
  account_id = int(account["number"])

  logging.info(f"Staring sync for {account_name}")

  cursor.execute(f"SELECT MAX(last_sync_date) FROM staging.sync_log WHERE account = '{table}';")
  max_sync_date = cursor.fetchone()[0]

  if max_sync_date is None:
    sync_start_date = datetime(2010, 1, 1, 0, 0, 0, 0, tz)
  elif max_sync_date >= now.date():
    logging.info(f"Sync skipped for {account_name} because start date {max_sync_date} is greater then {now}")
    continue
  else:
    sync_start_date = datetime.combine(max_sync_date, datetime.min.time()).astimezone(tz)

  # Get the list of months
  month_list = month_iter(sync_start_date)

  for month in month_list:
    logging.info(f"Syncing data - start_date: {month[0]} end_date: {month[1]}")
    get_insert_activities(month)

  insert_from_staging(table)

cursor.close()
connection.close()
logging.info(f"Closed connection to {db_database}")
