import time
from twilio.rest import Client
import requests
from dateutil import parser

# Create client
account_sid = ''  # Grab from Twilio
auth_token = ''  # Grab from Twilio
client = Client(account_sid, auth_token)

location_map = {
    "bowling_green": {
        "location_name": "Bowling Green",
        # Update the URL to match your location. (Use network monitor to find the URL in their appointment selector.)
        "location_id": "6480",
        # The last appointment that we've notified about, to prevent duplicate notifications
        "prev_start": None,
        # Placeholder last_checked time of (functionally) never
        "last_checked": 0
    },
    "jfk": {
        "location_name": "John F. Kennedy Airport",
        "location_id": "5140",
        "prev_start": None,
        "last_checked": 0
    },
    "newark": {
        "location_name": "Newark",
        "location_id": "5444",
        "prev_start": None,
        "last_checked": 0
    }
}


# Send a text message and print the message
def notify(message):
    print(message)
    message = client.messages.create(
        body=message,
        from_='',
        to=''
    )


def check(location):
    # Check if any appointments are available, and if so, notify
    # Return True on error

    resp = requests.get(
        f'https://ttp.cbp.dhs.gov/schedulerapi/slots?orderBy=soonest&limit=1&locationId={location["location_id"]}&minimum=1')

    if not resp.ok:
        notify(f'Failed with status code {resp.status_code}')
        return True

    appts = resp.json()
    if len(appts) > 0:
        appt = appts[0]
        # Placeholder start time in the far future
        start = appt.get('startTimestamp', '2099-01-01T00:00')
        # Prevent duplicates
        if start != location["prev_start"]:
            print(f'{start} appointment found at {location["location_name"]}')
            location["prev_start"] = start
            date = parser.parse(start)
            # Change these checks to whatever you need. For me, it's November 2023.
            if date.year == 2023 and date.month == 11 and date.day < 15:
                notify(f'{start} appointment found at {location["location_name"]}')
        else:
            print(f'Found 0 new appointments at {location["location_name"]}')
    else:
        print(f'Found 0 appointments at {location["location_name"]}')
    return False


if __name__ == '__main__':
    while True:
        current_time = time.time()
        checkedALocation = False

        for locationKey in location_map.keys():
            location = location_map[locationKey]
            if current_time - location["last_checked"] >= 60:
                if check(location):
                    # If an error is returned from the endpoint, set the next check time to 15 minutes from now.
                    location["last_checked"] = current_time + 900
                else:
                    location["last_checked"] = current_time
                checkedALocation = True

        # Separate out iterations of the for loop where at least one location endpoint is not erroring with a newline
        if checkedALocation:
            print('\n')

        # Calculate the minimum time until the next check and sleep accordingly
        next_check_times = [location_map[location]["last_checked"] for location in location_map.keys()]
        min_wait_time = min(next_check_times) - current_time
        if min_wait_time > 0:
            time.sleep(min_wait_time)
