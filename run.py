"""
To run the main function imidiatedly without waiting for scheduling
"""

from main import main
from main import telegram_send_alert
import pandas as pd

main()

# to check telegram api endpoint only
# telegram_send_alert(pd.DataFrame([{'alert': False},]))