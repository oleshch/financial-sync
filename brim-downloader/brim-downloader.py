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

# Brim Secrets
with open(file_path) as file:
  config = json.load(file)
  brim_username = config["brim_username"]
  brim_password = config["brim_password"]
  table = config["table"]

# Connect to Database
connection = psycopg2.connect(user = db_user,
                              password = db_password,
                              host = db_host,
                              port = db_port,
                              database = db_database)

cursor = connection.cursor()
logging.info(f"Connecting to database {db_database}")

def download_csv():
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
  logging.info(f"Opening browser session")
  browser.get("https://brimfinancial.com/webportal/Login")
  # User Name
  browser.find_elements_by_xpath('//*[@id="username"]')[0].send_keys(brim_username)
  # Password
  browser.find_elements_by_xpath('//*[@id="password"]')[0].send_keys(brim_password)
  # Login
  browser.find_elements_by_xpath('//*[@id="signin"]')[0].click()
  # Statement
  browser.get("https://brimfinancial.com/webportal/Activity/statement")
  # Download
  time.sleep(5)
  browser.find_elements_by_xpath('/html/body/div[1]/div[4]/div[2]/div[2]/section[1]/div/div/div[2]/div/div/a')[0].click()
  # Choose CSV
  browser.find_elements_by_xpath('/html/body/div[1]/div[4]/div[2]/div[2]/section[1]/div/div/div[2]/div/div/ul/li[1]/a')[0].click()

  download_date_raw = browser.find_elements_by_xpath('/html/body/div[1]/div[4]/div[2]/div[2]/section[1]/div/div/div[1]/div[1]/div/div/span')[0].text

  account = 'Brim Mastercard'
  year = download_date_raw.split(", ")[1]
  month = download_date_raw.split(" ")[0]
  download_date = datetime.strptime(month + " " + year, "%b %Y")

  cursor.execute(f"INSERT INTO staging.sync_log (account, last_sync_date) VALUES ('{account}','{download_date}');")
  browser.close()
  logging.info(f"Closed browser session")

def copy_csv_to_db(table):
  list_of_files = glob.glob(script_path + '/statement-*.csv')
  latest_file = max(list_of_files, key=os.path.getctime)

  with open(latest_file, 'r') as file:

    copy_sql = f"""
    COPY staging.{table} FROM stdin WITH CSV HEADER
    DELIMITER as ','
    """

    cursor.copy_expert(sql=copy_sql, file=file)
    logging.info(f"Loaded {table} into staging")
    connection.commit()
    file.close()

def insert_from_staging(table):

  insert_query = f"""
  INSERT INTO accounts.{table}
  (number
  , Transaction_Date
  ,Posted_Date
  ,Description
  ,Cardmember
  ,Amount
  ,Points
  ,CATEGORY)
  SELECT DISTINCT
    number
    , Transaction_Date
    , Posted_Date
    , Description
    , Cardmember
    , Amount
    , Points
    , CATEGORY
  FROM staging.{table}
  WHERE number || Transaction_Date || Posted_Date || Description || Cardmember || Amount || Points || CATEGORY NOT IN
    (
    SELECT
    number || Transaction_Date || Posted_Date || Description || Cardmember || Amount || Points || CATEGORY
    FROM accounts.{table}
    );
  """
  cursor.execute(insert_query)
  connection.commit()
  logging.info(f"Loaded {table} from staging")

# Main Procedure

download_csv()
copy_csv_to_db(table)
insert_from_staging(table)


cursor.close()
connection.close()
logging.info(f"Closed connection to {db_database}")


