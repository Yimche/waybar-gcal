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
SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]

def list_cal(service):
    print(f"List of all calendars")
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


def main():
  """Shows basic usage of the Google Calendar API.
  Prints the start and name of the next 10 events on the user's calendar.
  """
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
    service = build("calendar", "v3", credentials=creds)

    #list_cal(service)

    # Call the Calendar API
    now = datetime.datetime.now().astimezone().isoformat()
    #print("Getting the upcoming 10 events")
    # wattle
    events_result = (
        service.events().list(
            calendarId=os.environ['WATTLE'],
            timeMin=now,
            maxResults=10,
            singleEvents=True,
            orderBy="startTime",
        ).execute()
    )
    events = events_result.get("items", [])

    # canvas
    events_result = (
        service.events().list(
            calendarId=os.environ['CANVAS'],
            timeMin=now,
            maxResults=10,
            singleEvents=True,
            orderBy="startTime",
        ).execute()
    )
    events = events + events_result.get("items", [])

    # Manual Deadlines
    events_result = (
        service.events().list(
            calendarId=os.environ['MANUAL'],
            timeMin=now,
            maxResults=10,
            singleEvents=True,
            orderBy="startTime",
        ).execute()
    )
    events = events + events_result.get("items", [])

    if not events:
        print("No upcoming events found.")
        return

    events = [e for e in events if "Survey" not in e["summary"]]

    now = datetime.datetime.now().astimezone()  # local time
    
    # Tuple of (local_datetime, event)
    event_list = []
    for e in events:
        start_str = e["start"].get("dateTime", e["start"].get("date"))
        if "T" in start_str:  # timestamp with time
            start_dt = datetime.datetime.fromisoformat(start_str.replace("Z", "+00:00"))
            local_dt = start_dt.astimezone()
        else:  # all-day event
            local_dt = datetime.datetime.fromisoformat(start_str)
        event_list.append((local_dt, e))
    
    # Sort by local datetime
    event_list.sort(key=lambda x: x[0])
    
    # Remove old events file
    if os.path.exists("events.txt"):
        os.remove("events.txt")
    
    # Print sorted events
    for local_dt, event in event_list:
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
        
        line = f"{days_text} ({local_dt.strftime('%H:%M')}) - {event['summary']}"
        print(line)
        with open("events.txt", "a") as f:
            f.write(line + "\n")

  except HttpError as error:
    print(f"An error occurred: {error}")

if __name__ == "__main__":
    main()
