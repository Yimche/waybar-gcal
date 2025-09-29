#!./venv/bin/python

import datetime
import os.path

from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

load_dotenv()

# If modifying these scopes, delete the file token.json.
SCOPES = [
        "https://www.googleapis.com/auth/calendar.readonly",
        "https://www.googleapis.com/auth/tasks.readonly"
        ]


def list_cal(service):
    """
    Prints list of calendars available
    @type service: google calendar service object
    @param service: Api access service for the calendar
    @returns: List of available calendars
    """
    print("List of all calendars")
    print('Getting list of calendars')
    calendars_result = service.calendarList().list().execute()

    calendars = calendars_result.get('items', [])

    if not calendars:
        print('No calendars found.')
    for calendar in calendars:
        summary = calendar['summary']
        id = calendar['id']
        primary = "Primary" if calendar.get('primary') else ""
        print("%s\t%s\t%s" % (summary, id, primary))


def get_events(service, calendar: str):
    """
    Returns the list of events from a given calendar url
    @param service: google calendar service object
    @param calendar: url string pointing to the desired calendar
    @returns: List of events from calendar
    """

    now = datetime.datetime.now().astimezone().isoformat()
    events_result = (
        service.events().list(
            calendarId=os.environ[calendar],
            timeMin=now,
            maxResults=10,
            singleEvents=True,
            orderBy="startTime",
        ).execute()
    )
    events_list = events_result.get("items", [])
    return events_list


def list_tasklist(service):
    """
    Prints list of calendars available
    @type service: google calendar service object
    @param service: Api access service for the task list
    @returns: List of available google tasklists
    """
    print("List of all Task lists")
    print('Getting tasklists')
    try:
        results = service.tasklists().list(maxResults=10).execute()
        items = results.get("items", [])

        if not items:
            print("No task lists found.")
            return

        print("Task lists:")
        for item in items:
            print(f"{item['title']} ({item['id']})")
    except HttpError as err:
        print(err)


def sort_events(events):
    """
    Sorts list of events
    @param events_list: Events list
    @returns: Sorted events list
    """

    events_list = []

    for e in events:
        start_str = e["start"].get("dateTime", e["start"].get("date"))
        if "T" in start_str:  # timestamp with time
            start_dt = datetime.datetime.fromisoformat(start_str.replace(
                "Z", "+00:00")
            )
            local_dt = start_dt.astimezone()
        else:  # all-day event
            local_dt = datetime.datetime.fromisoformat(start_str).astimezone()
        events_list.append((local_dt, e))

    # Sort by local datetime
    events_list.sort(key=lambda x: x[0])
    return events_list


def main():
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json", SCOPES
            )
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open("token.json", "w") as token:
            token.write(creds.to_json())

    try:
        cal_service = build("calendar", "v3", credentials=creds)
        # list_cal(cal_service)

        # task_service = build("tasks", "v1", credentials=creds)
        # list_tasklist(task_service)

        events = []
        events = events + get_events(cal_service, 'WATTLE')
        events = events + get_events(cal_service, 'CANVAS')
        events = events + get_events(cal_service, 'MANUAL')

        if not events:
            print("No upcoming events found.")
            return

        events = [e for e in events if "Survey" not in e["summary"]]
        events = [e for e in events if "2100" not in e["summary"]]
        events = [e for e in events if "Quiz" and "opens" not in e["summary"]]

        events_list = sort_events(events)

        if events_list == []:
            with open("events.txt", "a") as f:
                f.write("No Assignments!" + "\n")
        else:
            now: datetime.datetime = datetime.datetime.now().astimezone()

            # Remove old events file
            if os.path.exists("events.txt"):
                os.remove("events.txt")

            # Print sorted events
            for local_dt, event in events_list:
                delta = local_dt - now
                days_remaining = delta.days
                if days_remaining == 0:
                    days_text = "Due today"
                elif days_remaining == 1:
                    days_text = "Due tomorrow"
                elif days_remaining <= 9:
                    days_text = f"Due in 0{days_remaining} days"
                else:
                    days_text = f"Due in {days_remaining} days"

                line = (
                        f"{days_text} ({local_dt.strftime('%H:%M')})"
                        f" - "
                        f"{event['summary']}"
                        )
                print(line)
                with open("events.txt", "a") as f:
                    f.write(line + "\n")

    except HttpError as error:
        print(f"An error occurred: {error}")


if __name__ == "__main__":
    main()
