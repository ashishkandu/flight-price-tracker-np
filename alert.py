import requests
import json
import pandas as pd
from types import SimpleNamespace as Namespace

import os
from dotenv import load_dotenv

from logging_ import log_setup
import logging

_ = log_setup()
logger = logging.getLogger(__name__)

load_dotenv()
API_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')


def generate_message(flight_details: Namespace) -> str:
    """Generate message for telegram alert"""
    msg = f"📬 The price for {flight_details.sectorpair}, {flight_details.flightdate} has just changed from *{flight_details.previousprice} NPR* to *{flight_details.price} NPR*\n\nThanks 🙏"
    return msg


def telegram_send_alert(msg_df: pd.DataFrame):

    # print(requests.get(url=f'https://api.telegram.org/bot{API_TOKEN}/getUpdates').content)
    if not msg_df[msg_df["alert"]].empty:
        rows = json.loads(json.dumps(msg_df[msg_df["alert"]].to_dict(
            'records')), object_hook=lambda d: Namespace(**d))
        for row in rows:
            response = requests.post(
                url=f'https://api.telegram.org/bot{API_TOKEN}/sendMessage',
                data={
                    "chat_id": TELEGRAM_CHAT_ID,
                    "parse_mode": "markdown",
                    "text": generate_message(row)
                }
            )
            logger.info(
                f'Msg sent to telegram with response code {response.status_code}')
        return True
    return False
