import time
from twilio.rest import Client
import requests
from datetime import datetime
from dateutil import parser
from dotenv import load_dotenv
import os
from config import API_URL_ENDING, BASE_API_URL, LOCATION_MAP, CHECK_INTERVAL, ERROR_RETRY_INTERVAL, TARGET_YEAR, \
    TARGET_MONTH, TARGET_DAY

# Load the variables from the .env file
load_dotenv()

# Create client
account_sid = os.getenv('ACCOUNT_SID')  # Grab from Twilio
auth_token = os.getenv('AUTH_TOKEN')  # Grab from Twilio
client = Client(account_sid, auth_token)


# Send a text message and print the message
def send_text_message(message):
    """Send a text message using the Twilio client."""
    print(message)
    client.messages.create(
        body=message,
        from_=os.getenv('TWILIO_PHONE_NUMBER'),  # Grab from Twilio (e.g. +12061231231)
        to=os.getenv('YOUR_PHONE_NUMBER')  # Insert your own phone number (e.g. +12067897897)
    )


def print_and_send_text_message(message):
    """Send the given message as a text to the user's phone number and print it as a message to the console."""
    print(message)
    send_text_message(message)


def get_more_readable_timestamp(timestamp):
    """Convert a timestamp string in the format of, for example, '2024-04-15T13:10' to '2024-04-15 at 13:10'"""
    return datetime.strptime(timestamp, '%Y-%m-%dT%H:%M').strftime('%Y-%m-%d at %H:%M')


def check_location_for_appointments_and_notify(current_location):
    """Check if any appointments are available for the given location, and, if so, notify the user.
    Returns true if no errors are encountered attempting to reach the endpoint; false otherwise.
    """
    try:
        resp = requests.get(f"{BASE_API_URL}{current_location['location_id']}{API_URL_ENDING}")
        if not resp.ok:
            print_and_send_text_message(f'Failed with status code {resp.status_code}')
            return False
    # Handle any exceptions that occur before the HTTP request completes
    except requests.RequestException as exception:
        print_and_send_text_message(f'Request failed: {exception}')
        return False

    available_appointments = resp.json()
    if len(available_appointments) > 0:
        # The appointment is always in a list of size 1, so we need to extract it and then the date and time.
        appointment_date_and_time = available_appointments[0].get('startTimestamp')

        # Notify the user if there is a different earliest appointment than one about which they have already
        # been notified
        if appointment_date_and_time != current_location["prev_appt_date_and_time"]:
            readable_timestamp = get_more_readable_timestamp(appointment_date_and_time)
            print(f'{readable_timestamp} appointment found at {current_location["location_name"]}')

            current_location["prev_appt_date_and_time"] = appointment_date_and_time

            # Send the text message
            date = parser.parse(appointment_date_and_time)
            # You can remove this check or parts of it if you want to be notified for any new appointments,
            # appointments in a month not before a specific day, etc.
            if date.year == TARGET_YEAR and date.month == TARGET_MONTH and date.day < TARGET_DAY:
                send_text_message(f'{readable_timestamp} appointment found at {current_location["location_name"]}')

        # The earliest available appointment is not different from the prior one
        else:
            print(f'Found 0 new appointments at {current_location["location_name"]}')

    # There are no appointments at all at this location
    else:
        print(f'Found 0 appointments at {current_location["location_name"]}')

    return True


if __name__ == '__main__':
    while True:
        current_time = time.time()
        checked_a_location = False

        for locationKey in LOCATION_MAP.keys():
            location = LOCATION_MAP[locationKey]
            if current_time - location["last_checked"] >= CHECK_INTERVAL:
                if not check_location_for_appointments_and_notify(location):
                    # If an error occurs, set the next check time for this location to 15 minutes from now.
                    location["last_checked"] = current_time + ERROR_RETRY_INTERVAL
                else:
                    location["last_checked"] = current_time
                checked_a_location = True

        # Separate out iterations of the for loop where at least one location endpoint is not erroring with a newline
        if checked_a_location:
            print('\n')

        # Calculate the minimum time until the next check and sleep accordingly.
        # i.e. if one location endpoint encountered an error and is waiting the duration of the error retry interval,
        # but another endpoint did not encounter an error, then we only wait the normal check interval.
        next_check_times = [LOCATION_MAP[location]["last_checked"] for location in LOCATION_MAP.keys()]
        min_wait_time = min(next_check_times) - current_time
        if min_wait_time > 0:
            time.sleep(min_wait_time)
