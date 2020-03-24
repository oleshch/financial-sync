#!/usr/bin/env python3

import os
import sys
import csv
import time
import glob
import json
import calendar
import logging
import psycopg2
from dateutil.rrule import rrule, MONTHLY
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.ui import Select

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

# Database fields
with open(db_file_path) as file:
  config = json.load(file)
  db_user = config["db_user"]
  db_password = config["db_password"]
  db_host = config["db_host"]
  db_port = config["db_port"]
  db_database = config["db_database"]

with open(file_path) as file:
  config = json.load(file)
  bcu_card_number = config["bcu_card_number"]
  bcu_password = config["bcu_password"]
  accounts = config["accounts"]

# Connect to Database
connection = psycopg2.connect(user = db_user,
                              password = db_password,
                              host = db_host,
                              port = db_port,
                              database = db_database)

cursor = connection.cursor()
logging.info(f"Connecting to database {db_database}")


def month_iter(start_month, start_year, end_month, end_year):
    start = datetime(start_year, start_month, 1)
    end = datetime(end_year, end_month, 1)
    return ((f"{d.month:02d}", d.year) for d in rrule(MONTHLY, dtstart=start, until=end))

def open_browser():
  options = Options()
  options.headless = True

  profile = webdriver.FirefoxProfile()
  profile.set_preference("browser.download.folderList", 2)
  profile.set_preference("browser.download.manager.showWhenStarting", False)
  profile.set_preference("browser.helperApps.alwaysAsk.force", False);
  profile.set_preference("browser.download.dir", script_path)
  profile.set_preference("browser.helperApps.neverAsk.saveToDisk", "text/csv,application/octet-stream,application/csv,")
  # Opening the Browser
  browser = webdriver.Firefox(firefox_profile=profile, options=options)
  browser.get("https://www.bculink.ca/")
  # Click Continue Button
  browser.find_elements_by_xpath('/html/body/div[2]/div[2]/div/div/div/div[5]/div/div/form/div/table/tbody/tr/td/input[1]')[0].click()
  # User Name
  browser.find_elements_by_xpath('/html/body/div[2]/div[2]/div/div/div/div[5]/div/div/form/table/tbody/tr[1]/td[3]/input[1]')[0].send_keys(bcu_card_number)
  # Password
  browser.find_elements_by_xpath('/html/body/div[2]/div[2]/div/div/div/div[5]/div/div/form/table/tbody/tr[1]/td[5]/input')[0].send_keys(bcu_password)
  # Login
  browser.find_elements_by_xpath('/html/body/div[2]/div[2]/div/div/div/div[5]/div/div/form/table/tbody/tr[2]/td/input[1]')[0].click()
  # Statements
  browser.find_elements_by_xpath('/html/body/div[2]/div[1]/div/div[2]/div[2]/div/ul/li[5]')[0].click()

  logging.info(f"Browser Opened")
  return browser

def copy_csv_to_db(downloaded_file_name, table):

  with open(downloaded_file_name) as input, open(downloaded_file_name[:-4]+'-clean.csv', 'w') as output:
      writer = csv.writer(output)
      for row in csv.reader(input):
          if any(field.strip() for field in row):
             writer.writerow(row)
      input.close()
      output.close()
      os.remove(downloaded_file_name)

  with open(downloaded_file_name[:-4]+'-clean.csv', 'r') as file:

    cursor.copy_from(file=file,
                     table=f"staging.{table}",
                     columns=('date', 'description', 'amount', 'balance'),
                     sep=',',
                     null='')
    connection.commit()
    file.close()


def loop_accounts(accounts):
  # Looping over Accounts

  for account_config in accounts:
    # Seting up variables
    account = account_config["account"]
    table = account_config["table"]
    account_safe_name = account.split(" - ",1)[0].replace(" ", "_")
    now = datetime.now().date()

    cursor.execute(f"SELECT MAX(last_sync_date) FROM staging.sync_log WHERE account = '{account}';")
    max_sync_date = cursor.fetchone()[0]

    if max_sync_date is None:
      sync_start_date = datetime.strptime('2011-01-01', '%Y-%m-%d').date()
    elif max_sync_date >= now:
      logging.info(f"Sync skipped for {account} because start date {max_sync_date} is greater then {now}")
      continue
    else:
      sync_start_date = max_sync_date

    logging.info(f"Starting Sync for {account} using start date of {sync_start_date}")

    # Loop over Months
    for m in month_iter(sync_start_date.month, sync_start_date.year, now.month, now.year):

      year=str(m[1])
      month=str(m[0])

      try:
        # Select Account
        account_dropdown = Select(browser.find_element_by_xpath('//*[@id="FrAccount"]'))
        account_dropdown.select_by_value(account)

        # Select Year

        year_dropdown = Select(browser.find_element_by_xpath('//*[@id="Year"]'))
        year_dropdown.select_by_value(year)

        # Select Month
        month_dropdown = Select(browser.find_element_by_xpath('/html/body/div[2]/div[2]/div/div/div/div[4]/div[1]/div/form/table/tbody/tr[3]/td[2]/select'))
        month_dropdown.select_by_value(month)

        # Click Download
        browser.find_elements_by_xpath('/html/body/div[2]/div[2]/div/div/div/div[4]/div[1]/div/form/table/tbody/tr[5]/td/input[1]')[0].click()
        time.sleep(5)
      except:
        logging.info(f"Something went wrong: {account} {year}-{month}")
        break

      try:
        # Click Back
        browser.find_elements_by_xpath('/html/body/div[2]/div[2]/div/div/div/div[4]/div/div/div/form/table/tbody/tr[2]/td/input[2]')[0].click()
        list_of_files = glob.glob(script_path + '/*.csv')
        latest_file = max(list_of_files, key=os.path.getctime)

        downloaded_file_name = script_path + f"/csvs/{year}-{month}-{account_safe_name}.csv"
        clean_file_name = script_path + f"/csvs/{year}-{month}-{account_safe_name}-clean.csv"

        os.rename(latest_file,downloaded_file_name)
        logging.info(f"Downloaded file: {downloaded_file_name}")
        cursor.execute(f"INSERT INTO staging.sync_log (account, last_sync_date) VALUES ('{account}','{year}-{month}-01');")

        copy_csv_to_db(downloaded_file_name, table)
      except:
        cursor.execute(f"INSERT INTO staging.sync_log (account, last_sync_date) VALUES ('{account}','{year}-{month}-01');")
        connection.commit()
        # Click Continue
        browser.find_elements_by_xpath('/html/body/div[2]/div[2]/div/div/div/div[4]/div/div/form/table/tbody/tr[2]/td/input')[0].click()
        # Statements
        browser.find_elements_by_xpath('/html/body/div[2]/div[1]/div/div[2]/div[2]/div/ul/li[5]')[0].click()

def insert_from_staging(accounts):

  for account_config in accounts:
    # Setting up variables
    table = account_config["table"]

    insert_query = f"""INSERT INTO accounts.{table}
    (date
    ,description
    ,amount
    ,balance)
    SELECT DISTINCT
      date
      , description
      , amount
      , balance
    FROM staging.{table}
    WHERE date || description || amount || balance NOT IN (SELECT
      date || description || amount || balance
    FROM accounts.{table});
    """
    cursor.execute(insert_query)
    connection.commit()
    logging.info(f"Loaded {table} from staging")


browser = open_browser()
loop_accounts(accounts)
insert_from_staging(accounts)

cursor.close()
connection.close()
logging.info(f"Closed connection to {db_database}")

browser.close()
logging.info(f"Closed browser session")