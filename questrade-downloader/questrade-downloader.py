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
from questrade_api import Questrade, Auth

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

def questrade_connect():
  """
  Connect to Questrade

  Returns
  =======
  q ,obj:
  Questrade connection Object
  """
  # Force Token Refresh
  q_auth = Auth(config=Questrade().config)
  token = q_auth.token['refresh_token']
  q_auth._Auth__refresh_token(token)

  try:
    q = Questrade()
  except Exception as e:
    logging.error(f"Connection Error: {e}")

  return q

def month_iter(start_date):
  """
  Returns a list of start and end dates from start_date to now()

  Parameters
  ==========
  start_date, datetime:
  The starts date used to start the iteration.

  Returns
  =======
  month_list ,list:
  Returns a list of start and end dates from start_date to now()
  """
  todays_date = now
  month_list = []
  for month_date in rrule(MONTHLY, dtstart=start_date.replace(day=1), until=todays_date):
    end_of_month = month_date + relativedelta(day=31)
    # If end_of_month is passed today
    if end_of_month >= todays_date:
      end_of_month = todays_date
    # If the start date is mid month
    if month_date < start_date:
        start_of_month = start_date
    else:
        start_of_month = month_date.replace(day=1)
    #If the start and end date are the same skip
    if start_of_month != end_of_month:
        month_list.append((start_of_month.isoformat(), end_of_month.isoformat()))
  return month_list


def get_insert_activities(q, cursor, account_id, table, month):
  """
  Makes the API calls to get account acctivity, saves the data into the staging
  table and updates the sync log table.

  Parameters
  ==========
  q, obj:          Questrade connection object
  cursor, obj:     psycopg2 connection object
  account_id, str: account_id of the account being processed
  table, str:      staging table name
  month, list:     the month that is being processed

  """
  start_date = month[0]
  end_date = month[1]

  try:
    logger.info(f"API call for {start_date}, {end_date}")
    account_month_info = q.account_activities(account_id, startTime=start_date, endTime=end_date)
  except Exception as e:
    logger.error(f"Error: {e}")

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
  logger.info(f"Updating the sync log to {end_date}")

  connection.commit()

def insert_from_staging(cursor, table):
  """
  Inserts the records from the Staging table into the production table

  Parameters
  ==========
  cursor, obj:     psycopg2 connection object
  table, str:      staging/production table name

  """
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


def main():
  cursor = connection.cursor()
  logging.info(f"Connecting to database {db_database}")

  q = questrade_connect()

  # Get account information from Questrade
  try:
    accounts = q.accounts
    accounts.get("accounts")
  except Exception as e:
    logger.error(f"Error: {e}")
    sys.exit(1)
  else:
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
      get_insert_activities(q, cursor, account_id, table, month)

    insert_from_staging(cursor, table)

  cursor.close()
  connection.close()
  logging.info(f"Closed connection to {db_database}")

if __name__ == "__main__":
  main()