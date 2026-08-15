#!./venv/bin/python

import datetime
import os.path

from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.exceptions import RefreshError
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
    @returns: Sorted list of (local_dt, all_day, event) tuples
    """

    events_list = []

    for e in events:
        start_str = e["start"].get("dateTime", e["start"].get("date"))
        all_day = "T" not in start_str
        if all_day:  # date only, starts at local midnight
            local_dt = datetime.datetime.fromisoformat(start_str).astimezone()
        else:  # timestamp with time
            start_dt = datetime.datetime.fromisoformat(start_str.replace(
                "Z", "+00:00")
            )
            local_dt = start_dt.astimezone()
        events_list.append((local_dt, all_day, e))

    # Sort by local datetime
    events_list.sort(key=lambda x: x[0])
    return events_list


def due_text(local_dt, now):
    """
    Describes how far away an event is in calendar days, not elapsed time.
    @param local_dt: Event start, as a local-timezone datetime
    @param now: Current local-timezone datetime
    @returns: Human readable "Due ..." string
    """

    days_remaining = (local_dt.date() - now.date()).days

    if days_remaining < 0:
        return "Overdue"
    if days_remaining == 0:
        return "Due today"
    if days_remaining == 1:
        return "Due tomorrow"
    return f"Due in {days_remaining:02d} days"


def main():
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    try:
        creds = None
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
        cal_service = build("calendar", "v3", credentials=creds)

        # list_cal(cal_service)

        # task_service = build("tasks", "v1", credentials=creds)
        # list_tasklist(task_service)

        events = []

        calendars = [
                'WATTLE',
                'CANVAS',
                'MANUAL',
                ]

        for calendar in calendars:
            events = events + get_events(cal_service, calendar)

        events = [e for e in events if "Survey" not in e["summary"]]
        events = [e for e in events if "2100" not in e["summary"]]
        events = [e for e in events if "END" not in e["summary"]]
        events = [e for e in events if "Quiz" and "opens" not in e["summary"]]
        events = [e for e in events if "Lab test Week 12 - CODE + CONCEPT submission" not in e["summary"]]
        events = [e for e in events if "OFFLINE REFERENCE MATERIALS" not in e["summary"]]

        events_list = sort_events(events)

        if events_list == []:
            if os.path.exists("events.txt"):
                os.remove("events.txt")
            with open("events.txt", "a") as f:
                f.write("No Assignments!" + "\n")
        else:
            now: datetime.datetime = datetime.datetime.now().astimezone()

            # Remove old events file
            if os.path.exists("events.txt"):
                os.remove("events.txt")

            PREFIX_WIDTH = 25

            # Print sorted events
            for local_dt, all_day, event in events_list:
                days_text = due_text(local_dt, now)
                time_text = "all day" if all_day else local_dt.strftime("%H:%M")

                summary = event["summary"]
                if len(summary) > 42:
                    summary = summary[:41] + "…"

                prefix = f"{days_text} ({time_text})"
                line = f"{prefix:<{PREFIX_WIDTH}}{summary}"

                print(line)
                with open("events.txt", "a") as f:
                    f.write(line + "\n")

    except HttpError as error:
        print(f"An error occurred: {error}")

    except RefreshError as error:
        print(f"Token has expired: {error}")

if __name__ == "__main__":
    main()
