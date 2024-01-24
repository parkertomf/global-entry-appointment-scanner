import time
from twilio.rest import Client
import requests
from dateutil import parser
from dotenv import load_dotenv
import os
from config import API_URL_ENDING, BASE_API_URL, LOCATION_MAP, CHECK_INTERVAL, ERROR_RETRY_INTERVAL, TARGET_YEAR, TARGET_MONTH, TARGET_DAY

# Load the variables from .env file
load_dotenv()

# Create client
account_sid = os.getenv('ACCOUNT_SID')  # Grab from Twilio
auth_token = os.getenv('AUTH_TOKEN')  # Grab from Twilio
client = Client(account_sid, auth_token)

# Send a text message and print the message
def notify(message):
    print(message)
    message = client.messages.create(
        body=message,
        from_=os.getenv('TWILIO_PHONE_NUMBER'),  # Grab from Twilio (e.g. +12061231231)
        to=os.getenv('YOUR_PHONE_NUMBER')  # Insert your own phone number (e.g. +12067897897)
    )


def check(current_location):
    # Check if any appointments are available, and if so, notify
    # Return False on error

    resp = requests.get(f"{BASE_API_URL}{current_location['location_id']}{API_URL_ENDING}")

    if not resp.ok:
        notify(f'Failed with status code {resp.status_code}')
        return False

    appts = resp.json()
    if len(appts) > 0:
        appt = appts[0]
        # Placeholder start time in the far future
        start = appt.get('startTimestamp', '2099-01-01T00:00')
        # Prevent duplicates
        if start != current_location["prev_start"]:
            print(f'{start} appointment found at {current_location["location_name"]}')
            current_location["prev_start"] = start
            date = parser.parse(start)
            # You can remove this check or parts of it if you want to be notified for any new appointments,
            # appointments in a month not before a specific day, etc.
            if date.year == TARGET_YEAR and date.month == TARGET_MONTH and date.day < TARGET_DAY:
                notify(f'{start} appointment found at {current_location["location_name"]}')
        else:
            print(f'Found 0 new appointments at {current_location["location_name"]}')
    else:
        print(f'Found 0 appointments at {current_location["location_name"]}')
    return True


if __name__ == '__main__':
    while True:
        current_time = time.time()
        checkedALocation = False

        for locationKey in LOCATION_MAP.keys():
            location = LOCATION_MAP[locationKey]
            if current_time - location["last_checked"] >= CHECK_INTERVAL:
                if not check(location):
                    # If an error is returned from the endpoint, set the next check time to 15 minutes from now.
                    location["last_checked"] = current_time + ERROR_RETRY_INTERVAL
                else:
                    location["last_checked"] = current_time
                checkedALocation = True

        # Separate out iterations of the for loop where at least one location endpoint is not erroring with a newline
        if checkedALocation:
            print('\n')

        # Calculate the minimum time until the next check and sleep accordingly
        next_check_times = [LOCATION_MAP[location]["last_checked"] for location in LOCATION_MAP.keys()]
        min_wait_time = min(next_check_times) - current_time
        if min_wait_time > 0:
            time.sleep(min_wait_time)
