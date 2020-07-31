#!/usr/bin/env python3

import os
import sys
import json
import time
import glob
import logging
import psycopg2
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

# TD Secrets
with open(file_path) as file:
  config = json.load(file)
  brim_username = config["td_username"]
  brim_password = config["td_password"]
  table = config["table"]

def connect_to_db(db_user, db_password, db_host, db_port, db_database):
  # Connect to Database
  connection = psycopg2.connect(user = db_user,
                                password = db_password,
                                host = db_host,
                                port = db_port,
                                database = db_database)

  cursor = connection.cursor()
  return connection, cursor
  logging.info(f"Connecting to database {db_database}")

def download_csv():
  options = Options()
  options.headless = True

  profile = webdriver.FirefoxProfile()
  profile.set_preference("browser.download.folderList", 2)
  profile.set_preference("browser.download.manager.showWhenStarting", False)
  profile.set_preference("browser.helperApps.alwaysAsk.force", False);
  profile.set_preference("browser.download.dir", script_path + '/csvs')
  profile.set_preference("browser.helperApps.neverAsk.saveToDisk", "text/csv,application/octet-stream,application/csv,")
  # Opening the Browser
  browser = webdriver.Firefox(firefox_profile=profile, options=options)
  logging.info(f"Opening browser session")
  browser.get("https://authentication.td.com/uap-ui/index.html?consumer=easyweb&locale=en_CA#/login/easyweb-getting-started")
  # User Name
  browser.find_elements_by_xpath('//*[@id="username100"]')[0].send_keys(brim_username)
  # Password
  browser.find_elements_by_xpath('//*[@id="password"]')[0].send_keys(brim_password)
  # Login
  browser.find_elements_by_xpath('//*[@id="loginForm"]/div/div/div[4]/div/div/button')[0].click()
  time.sleep(5)
  # Download Checkbox
  browser.find_elements_by_xpath('//*[@id="td-layout-contentarea"]/div[2]/div[2]/div/div[7]/table/tbody/tr[2]/td[2]/input')[0].click()
  # Download Button
  browser.find_elements_by_xpath('//*[@id="download_button"]')[0].click()
  browser.close()
  logging.info(f"Closed browser session")

def copy_csv_to_db(connection, cursor, table):
  list_of_files = glob.glob(script_path + '/csvs/accountactivity.csv')
  latest_file = max(list_of_files, key=os.path.getctime)

  with open(latest_file, 'r') as file:

    copy_sql = f"""
    COPY staging.{table}
    FROM stdin
    DELIMITER as ','
    NULL as ''
    CSV;
    """

    cursor.copy_expert(sql=copy_sql, file=file)
    logging.info(f"Loaded {table} into staging")
    connection.commit()
    file.close()


def update_sync_log(connection, cursor, account):
  now = datetime.now()
  cursor.execute(f"INSERT INTO staging.sync_log (account, last_sync_date) VALUES ('{account}','{now}');")
  logging.info(f"Updated sync_log table for {account} with date: {now}")
  connection.commit()


def insert_from_staging(connection, cursor, table):

  insert_query = f"""
  INSERT INTO accounts.{table}
  (
   date
  ,transaction_description
  ,debit
  ,credit
  ,balance
  )
  SELECT DISTINCT
     date
    , transaction_description
    , debit
    , credit
    , balance
  FROM staging.{table}
  WHERE concat(date, transaction_description, debit, credit,balance) NOT IN
    (
    SELECT
    concat(date, transaction_description, debit, credit,balance)
    FROM accounts.{table}
    );
  """
  cursor.execute(insert_query)
  connection.commit()
  logging.info(f"Loaded {table} from staging")


def close_db_connection(connection, cursor):
  cursor.close()
  connection.close()
  logging.info(f"Closed connection to {db_database}")

def main():
  # Main Procedure

  download_csv()

  connection, cursor = connect_to_db(db_user, db_password, db_host, db_port, db_database)
  copy_csv_to_db(connection, cursor, table)
  update_sync_log(connection, cursor, account='td_visa')
  insert_from_staging(connection, cursor, table)
  close_db_connection(connection, cursor)

if __name__ == "__main__":
    main()

