#!/usr/bin/env python3

import os
import sys
import json
from pushbullet import Pushbullet

# Read Config File
script_path=os.path.dirname(os.path.realpath(__file__))
file_path =  os.path.join(script_path, 'config.json')

# Pushbullet Secrets
with open(file_path) as file:
  config = json.load(file)
  api_key = config["api_key"]

pb = Pushbullet(api_key)

lines =  sys.stdin.read()
push = pb.push_note("Financial Sync Error", lines)