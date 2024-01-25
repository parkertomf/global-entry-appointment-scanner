# The locations for which you want to check appointments.
LOCATION_MAP = {
    0: {
        # This can be whatever you want that makes the location identifiable to you in notifications.
        "location_name": "Bowling Green",
        # Update the URL to match your location. (Use network monitor to find the URL in their appointment selector.)
        "location_id": "6480",
        # The last appointment that we've notified about, to prevent duplicate notifications
        "prev_appt_date_and_time": None,
        # Placeholder last_checked time of (functionally) never
        "last_checked": 0
    },
    1: {
        "location_name": "John F. Kennedy Airport",
        "location_id": "5140",
        "prev_appt_date_and_time": None,
        "last_checked": 0
    },
    2: {
        "location_name": "Newark",
        "location_id": "5444",
        "prev_appt_date_and_time": None,
        "last_checked": 0
    }
}

# Parts of the endpoint to check for appointments at a location
BASE_API_URL = "https://ttp.cbp.dhs.gov/schedulerapi/slots?orderBy=soonest&limit=1&locationId="
API_URL_ENDING = "&minimum=1"

# Target appointment date settings (the script will check for any appointments before this date).
TARGET_YEAR = 2023
TARGET_MONTH = 11
TARGET_DAY = 15

# Time to wait between checks with and without failure on request.
CHECK_INTERVAL = 60  # seconds
ERROR_RETRY_INTERVAL = 900  # seconds
