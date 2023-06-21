import requests

from urls import Url
from logging_ import log_setup
import logging

_ = log_setup()
logger = logging.getLogger(__name__)


class FlightsData:
    """Represents flights data from internet for specified period of time"""
    
    def __init__(self, source='BWA', destination='KTM') -> None:
        self.headers = {
            'authority': 'www.buddhaair.com',
            'accept': 'application/json, text/plain, */*',
            'accept-language': 'en-IN,en-US;q=0.9,en;q=0.8,ms-MY;q=0.7,ms;q=0.6,en-GB;q=0.5',
            'content-type': 'application/json',
            'origin': 'https://www.buddhaair.com',
            'referer': f'https://www.buddhaair.com/search/flight?sector={source}-{destination}',
            'sec-ch-ua': '"Not.A/Brand";v="8", "Chromium";v="114", "Google Chrome";v="114"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Linux"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
        }

        self.source = source
        self.destination = destination
        

    def getFlightDetails(self, search_date: str) -> requests.Response:
        """Returns response of flight details for a given search date"""

        data = {
            'strSectorFrom': self.source,
            'strSectorTo': self.destination,
            'strReturnDate': None,
            'strFlightDate': search_date,
            'strNationality': 'NP',
            'strTripType': 'O',
            'intAdult': 1,
            'intChild': 0,
        }
        logger.info(f"Checking flight details for {search_date}")
        response = requests.post(
            Url.FlightAvailability, headers=self.headers, json=data)
        # print(response.json()['data']['outbound']['flightsector']['flightdetail'][-1]['flightdate']) # To see the response timings
        return response