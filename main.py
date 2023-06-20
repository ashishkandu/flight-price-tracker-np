import json
import pandas as pd
from types import SimpleNamespace as Namespace
from datetime import datetime, timedelta
from typing import Tuple
from concurrent.futures import ThreadPoolExecutor
import os

from fetch_flight_data import FlightsData


SAVE_TO_CSV = True
FLIGHTS_CSV = 'flights.csv'
TARGET_PRICE = 4500.0


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
    with ThreadPoolExecutor(max_workers=check_for_days) as executor:
        responses = executor.map(flight_data.getFlightDetails, dates)

    for response in responses:
        data = json.loads(response.content,
                          object_hook=lambda d: Namespace(**d))
        if data.data.outbound.flightsector == "":
            print('Flight detials not found!\n')
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
        flight_detail['alert'] = flight.price == previous_data[previous_data['flightdate'] ==
                                                               flight.flightdate]['price'].values[-1] != flight.price if not first_run else flight.price < TARGET_PRICE
        flight_detail['timestamp'] = datetime.now()
        flight_details.append(flight_detail)
    return pd.DataFrame(flight_details)


if __name__ == '__main__':
    first_run: bool = not os.path.exists(FLIGHTS_CSV)
    previous_df = None
    if not first_run:
        previous_df = pd.read_csv(FLIGHTS_CSV)
    flights_data = FlightsData()

    flights_df = process_flight_details(flights_data, previous_df, 15)
    print(flights_df.to_string(index=False))
    if SAVE_TO_CSV:
        flights_df.to_csv(FLIGHTS_CSV, index=False, mode="a",
                          header=not os.path.exists(FLIGHTS_CSV))
