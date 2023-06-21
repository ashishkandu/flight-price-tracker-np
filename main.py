import json
import pandas as pd
from types import SimpleNamespace as Namespace
from datetime import datetime, timedelta
from typing import Tuple
from concurrent.futures import ThreadPoolExecutor
import os
import requests
from dotenv import load_dotenv

import schedule
from schedule import repeat, every
import time

from fetch_flight_data import FlightsData
from logging_ import log_setup
import logging

_ = log_setup()
logger = logging.getLogger(__name__)

SAVE_TO_CSV = True
FLIGHTS_CSV = 'flights.csv'
PING_TELEGRAM = True
TARGET_PRICE = 4500.0
CHECKFORDAYS = 15
USE_THREAD = True

load_dotenv()
API_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

def find_cheapest_flight(flights: Namespace) -> Tuple[Namespace, float]:
    """Retrun the flight having lowest fare regardless of the flight classcode."""
    fares = {}
    for flight in flights:
        if flight.airfare.faredetail == '':
            continue
        faredetail = flight.airfare.faredetail
        total_fare = float(faredetail.fare) + float(faredetail.surcharge) + \
            float(faredetail.taxbreakup.taxdetail.taxamount) - \
            float(faredetail.cashback)
        fares[total_fare] = flight
    # finds lowest fare in the list of keys[total_fare]
    lowest_fare = min(fares.keys())
    # get the flight with lowest fare from above
    flight = fares.get(lowest_fare)
    # create new attribute price in the namespace
    flight.price = lowest_fare  
    return flight


def get_dates(days: int):
    today_full_date = datetime.now()
    date = today_full_date - timedelta(days=1)
    return [datetime.strftime(date := date + timedelta(days=1), "%d-%b-%Y") for _ in range(days)]


def process_flight_details(flight_data: FlightsData, previous_data: pd.DataFrame, check_for_days=7):
    flight_details = []
    dates = get_dates(check_for_days)
    if USE_THREAD:
        with ThreadPoolExecutor(max_workers=check_for_days) as executor:
            responses = executor.map(flight_data.getFlightDetails, dates)
    else:
        responses = map(flight_data.getFlightDetails, dates)

    for response in responses:
        data = json.loads(response.content,
                          object_hook=lambda d: Namespace(**d))
        if data.data.outbound.flightsector == "":
            logging.warning('[x] Flight detials not found!')
            continue
        flight_detail = {}
        flights = data.data.outbound.flightsector.flightdetail
        flight = find_cheapest_flight(flights)
        flight_detail['flightdate'] = flight.flightdate
        flight_detail['flightno'] = flight.flightno
        flight_detail['classcode'] = flight.classcode
        flight_detail['sectorpair'] = flight.sectorpair
        flight_detail['departuretime'] = flight.departuretime
        flight_detail['arrivaltime'] = flight.arrivaltime
        flight_detail['freebaggage'] = flight.freebaggage
        flight_detail['refundable'] = flight.refundable
        flight_detail['price'] = flight.price
        flight_detail['alert'] = previous_data[previous_data['flightdate'] == flight.flightdate]['price'].values[-1] != flight.price if not previous_data[previous_data['flightdate'] == flight.flightdate].empty else False
        flight_detail['timestamp'] = datetime.now()
        flight_details.append(flight_detail)
    return pd.DataFrame(flight_details)


def telegram_alert(msg_df: pd.DataFrame):
    if not msg_df[msg_df["alert"]].empty:
        response = requests.post(
            url=f'https://api.telegram.org/bot{API_TOKEN}/sendMessage',
            data={
                "chat_id": TELEGRAM_CHAT_ID,
                "parse_mode": "markdown",
                "text": msg_df[msg_df["alert"]].to_markdown(index=False)
            }
        ).status_code
        return response
    return False


@repeat(every(20).seconds)
def main():
    logger.info("Running checks...")
    first_run: bool = not os.path.exists(FLIGHTS_CSV)
    if first_run:
        logger.info("First run detected")
    previous_df = None
    if not first_run:
        logger.info("Loading previous data...")
        previous_df = pd.read_csv(FLIGHTS_CSV)
    flights_data = FlightsData()

    try:
        logger.info("Processing flight details...")
        flights_df = process_flight_details(flights_data, previous_df, CHECKFORDAYS)
    except Exception as e:
        logger.exception(e)
        return
    # print(flights_df.to_string(index=False))
    if SAVE_TO_CSV:
        logger.info(f"Saving report to {FLIGHTS_CSV}")
        flights_df.to_csv(FLIGHTS_CSV, index=False, mode="a",
                        header=not os.path.exists(FLIGHTS_CSV))
    if PING_TELEGRAM:
        is_sent = telegram_alert(flights_df)
        logger.info(f"Msg sent to telegram: {is_sent}")


if __name__ == '__main__':
    logger.info("Program started!")
    while True:
        schedule.run_pending()
        time.sleep(1)