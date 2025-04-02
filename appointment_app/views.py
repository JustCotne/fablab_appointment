from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import logout, authenticate, login as auth_login
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .forms import CreateUserForm, LaserBookingForm, ConsultationBookingForm
from collections import defaultdict
from django.http import HttpResponse
from django.conf import settings
from django.contrib.auth import get_user_model
from datetime import datetime, timedelta, UTC
from .models import Booking
from django.http import JsonResponse
from django.utils.timezone import now, make_aware, get_current_timezone
from django.core.mail import send_mail
from django.template.loader import render_to_string
import os
import pickle
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from urllib.parse import urlencode
import icalendar
from django.core.mail import EmailMessage
from google.oauth2 import service_account
import pytz
from googleapiclient.errors import HttpError
from django.utils.translation import activate



def custom_404_view(request, exception):
    return render(request, 'errors/404.html', status=404)
def custom_500(request):
    return render(request, 'errors/500.html', status=500)

def redirect_to_home_or_login(request):
    if request.user.is_authenticated:
        return redirect('home')
    return redirect('login')


def login(request):
    """Handles user login with email instead of username."""
    User = get_user_model()


    # Handle language switching
    if "language" in request.GET:
        language = request.GET["language"]
        if language in ["ka", "en"]:  # Allowed languages
            request.session["language"] = language  # Store in session
            activate(language)  # Change language immediately
        return redirect("login")  # Redirect to apply changes

    # Default to Georgian if not set
    language = request.session.get("language", "ka")


    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            messages.error(request, "ელ.ფოსტა არ არის რეგისტრირებული.")
            return render(request, "login.html")

        if user.is_deactivated:  # 🚀 Block deactivated users
            messages.error(request, "თქვენი ანგარიში დეაქტივირებულია, დამატებითი ინფორმაციის შემთხვევაში დაუკავშირდით Fablab iliauni-ის გუნდს.")
            return redirect("login")

        user = authenticate(request, username=user.username, password=password)
        if user:
            auth_login(request, user)
            return redirect("home")
        else:
            messages.error(request, "პაროლი ან ელ.ფოსტა არასოწრია, გთხოვთ ცადოთ ახლიდან!")

    return render(request, "login.html",{"language": language})


def register(request):
    """User registration page."""
    form = CreateUserForm()

    # Handle language switching
    if "language" in request.GET:
        language = request.GET["language"]
        if language in ["ka", "en"]:  # Allowed languages
            request.session["language"] = language  # Store in session
            activate(language)  # Change language immediately
        return redirect("register")  # Redirect to apply changes

    # Default to Georgian if not set
    language = request.session.get("language", "ka")

    if request.method == "POST":
        form = CreateUserForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("login")

    return render(request, "register.html", {"form": form, "language": language})


def logoutUser(request):
    logout(request)
    return redirect('login')


@login_required
def home(request):
    """Home page view."""

    check_and_send_reminders()

    if request.user.is_deactivated: 
        messages.error(request, "Your account is deactivated.")
        return redirect("logout")
    
        # Handle language switching
    if "language" in request.GET:
        language = request.GET["language"]
        if language in ["ka", "en"]:  # Allowed languages
            request.session["language"] = language  # Store in session
            activate(language)  # Change language immediately
        return redirect("home")  # Redirect to apply changes

    # Default to Georgian if not set
    language = request.session.get("language", "ka")
    context = {"language": language}
    return render(request, "home.html", context)



SERVICES = {
    "laser_cutting": "ლაზერული ჭრა",
    "3d_printing": "3D პრინტერი",
    "cnc": "პროგრამირებადი ჩარხი",
    "consultation": "კონსულტაცია"
}

def get_booked_slots():
    booked_slots = {}
    bookings = Booking.objects.all()

    for booking in bookings:
        key = f"{booking.date}-{booking.time}"
        if key not in booked_slots:
            booked_slots[key] = []
        booked_slots[key].append(booking.service)
    
    return booked_slots

def is_available(service, date, time):
    booked_slots = get_booked_slots()
    key = f"{date}-{time}"

    if key in booked_slots:
        booked_services = booked_slots[key]

        if service == "consultation":
            return "consultation" not in booked_services
        else:
            if service in booked_services:
                return False
            return len(booked_services) < 2
    
    return True

def generate_time_slots(service):
    """
    Generate available time slots dynamically based on service type.
    """
    if service == "laser_cutting":
        start_time = datetime.strptime("10:30", "%H:%M")
        end_time = datetime.strptime("17:30", "%H:%M")
        slot_duration = timedelta(minutes=120)
    else:
        start_time = datetime.strptime("14:00", "%H:%M")
        end_time = datetime.strptime("15:59", "%H:%M")
        slot_duration = timedelta(minutes=30) 

    slots = []
    while start_time <= end_time:
        slots.append(start_time.strftime("%H:%M"))
        start_time += slot_duration

    return slots

def generate_available_dates(service):
    today = datetime.today().date()
    start_date = today + timedelta(days=7) if service in ["laser_cutting", "3d_printing", "cnc"] else today
    available_dates = []
    days_added = 0

    while days_added < 14:
        if start_date.weekday() < 5:
            available_dates.append(start_date.strftime("%Y-%m-%d"))
            days_added += 1
        start_date += timedelta(days=1)

    return available_dates



@login_required
def calendar_view(request):
    """Calendar page view with language support."""

    if "language" in request.GET:
        language = request.GET["language"]
        if language in ["ka", "en"]:  # Allowed languages
            request.session["language"] = language
            activate(language)
        return redirect("calendar")  # Redirect to apply changes

    language = request.session.get("language", "ka")

    service = request.GET.get("service")

    if not service:
        return redirect("home")

    if service not in SERVICES:
        return render(request, "appointment_app/error.html", {"message": "Invalid Service Selected", "language": language})

    available_dates = generate_available_dates(service)
    time_slots = generate_time_slots(service)
    filtered_slots = {}

    for date in available_dates:
        available_times = []

        for time in time_slots:
            existing_bookings = Booking.objects.filter(date=date, time=time)
            service_bookings = existing_bookings.exclude(service="consultation")
            consultation_bookings = existing_bookings.filter(service="consultation")

            if service == "consultation":
                if not consultation_bookings.exists():
                    available_times.append(time)
            else:
                if service_bookings.count() < 2 and not service_bookings.filter(service=service).exists():
                    available_times.append(time)

        filtered_slots[date] = available_times

    return render(request, "calendar.html", {
        "language": language,
        "service": service,
        "service_name": SERVICES[service],
        "available_dates": available_dates,
        "time_slots": filtered_slots
    })



@login_required
def booking_view(request):
    service = request.GET.get("service")
    date = request.GET.get("date")
    time = request.GET.get("time")

    if not service or not date or not time:
        return redirect("calendar")

    # Check booking limit
    if request.user.booking_limit <= 0:
        return redirect("reach_limit")

    form_class = ConsultationBookingForm if service == "consultation" else LaserBookingForm

    if request.method == "POST":
        form = form_class(request.POST, request.FILES)
        if form.is_valid():
            booking = form.save(commit=False)
            booking.user = request.user
            booking.first_name = request.user.first_name
            booking.last_name = request.user.last_name
            booking.phone_number = request.user.phone_number
            booking.email = request.user.email

            # Deduct 1 from booking limit
            request.user.booking_limit -= 1
            request.user.save()

            if service == "consultation" and form.cleaned_data.get("meeting_type") == "online":
                booking.meeting_link = create_google_meet_link(booking)
                send_meeting_email(request.user, booking)
            else:
                send_confirmation_email(request.user, booking)

            event_id = add_event(booking, 20, booking.service) if service == "consultation" else add_event(booking, 90, booking.service_type)

            if event_id:
                booking.google_calendar_event_id = event_id
                booking.save()

            return redirect("home")

    else:
        form = form_class(initial={
            "first_name": request.user.first_name,
            "last_name": request.user.last_name,
            "phone_number": request.user.phone_number,
            "email": request.user.email,
            "service": service,
            "date": date,
            "time": time
        })

    return render(request, "booking.html", {"form": form, "service": service})



@login_required
def my_appointments(request):
    """Show user's booked appointments with cancellation and report options."""
    user_bookings = Booking.objects.filter(user=request.user).order_by("date", "time")

    appointments = []
    tz = get_current_timezone()

    for booking in user_bookings:
        appointment_datetime = datetime.combine(booking.date, booking.time)
        appointment_datetime = make_aware(appointment_datetime, timezone=tz)

        duration = booking.duration if hasattr(booking, "duration") else 60
        end_time = appointment_datetime + timedelta(minutes=duration)

        can_report = now() >= end_time

        time_difference = appointment_datetime - now()
        can_cancel = False
        if booking.service == "consultation":
            can_cancel = time_difference.total_seconds() >= 3600
        else:
            can_cancel = time_difference.days >= 4

        appointments.append({
            "id": booking.id,
            "service": booking.service,
            "date": booking.date,
            "time": booking.time,
            "can_cancel": can_cancel,
            "can_report": can_report
        })
    
    if "language" in request.GET:
        language = request.GET["language"]
        if language in ["ka", "en"]: 
            request.session["language"] = language  
            activate(language)
        return redirect("my_appointments")

    language = request.session.get("language", "ka")


    return render(request, "my_appointments.html", {"appointments": appointments,"language": language})



@login_required
def cancel_booking(request, booking_id):
    """Allow users to cancel their bookings if within allowed time limits."""
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)

    tz = get_current_timezone()
    appointment_datetime = datetime.combine(booking.date, booking.time)
    appointment_datetime = make_aware(appointment_datetime, timezone=tz)

    time_difference = appointment_datetime - now()

    if booking.service == "consultation":
        if time_difference.total_seconds() < 3600:  
            return redirect("my_appointments")
    else:
        if time_difference.days < 4:  
            return redirect("my_appointments")

    if booking.google_calendar_event_id:
        delete_calendar_event(booking.google_calendar_event_id)


    booking.delete()
    send_cancelation_email(request.user)
    return redirect("my_appointments")



@login_required
def report_view(request, booking_id):
    user = request.user  

    booking = get_object_or_404(Booking, id=booking_id, user=user)

    user_data = {
        "first_name": user.first_name,
        "last_name": user.last_name,
        "email": user.email,
        "phone_number": user.phone_number,
        "faculty": user.faculty,
        "program": user.program,
        "service": booking.service,
        "project_description": booking.project_details,
    }

    return render(request, "report.html", {"user_data": user_data})




def generate_ics_file(booking, user):
    """
    Generate an ICS file for the booking with RSVP options.
    """
    cal = icalendar.Calendar()
    cal.add('prodid', '-//Fablab Iliauni//Booking//EN')
    cal.add('version', '2.0')
    cal.add('method', 'REQUEST') 

    event = icalendar.Event()
    event.add('summary', f"Appointment: {booking.service}")
    event.add('dtstart', datetime.combine(booking.date, booking.time))
    event.add('dtend', datetime.combine(booking.date, booking.time) + timedelta(minutes=booking.duration if hasattr(booking, "duration") else 60))
    event.add('dtstamp', datetime.now())
    event.add('location', "Fablab Iliauni")
    event.add('description', f"Booking for {booking.service} at Fablab Iliauni.")


    organizer_email = "fablab@iliauni.edu.ge"
    event.add('organizer', f"MAILTO:{organizer_email}")

    event.add('attendee', f"MAILTO:{user.email}", {"RSVP": "TRUE"})
    event.add('attendee', f"MAILTO:{organizer_email}", {"RSVP": "TRUE"})

    cal.add_component(event)
    return cal.to_ical()

def generate_google_calendar_link(booking):
    """
    Generate a Google Calendar event creation URL with RSVP.
    """
    base_url = "https://www.google.com/calendar/render"
    start_time = datetime.combine(booking.date, booking.time).strftime("%Y%m%dT%H%M%S")
    end_time = (datetime.combine(booking.date, booking.time) + timedelta(minutes=booking.duration if hasattr(booking, "duration") else 60)).strftime("%Y%m%dT%H%M%S")

    params = {
        "action": "TEMPLATE",
        "text": f"Appointment: {booking.service}",
        "dates": f"{start_time}/{end_time}",
        "details": f"Booking for {booking.service} at Fablab Iliauni.",
        "location": "Fablab Iliauni",
        "sf": "true",
        "output": "xml"
    }
    
    return f"{base_url}?{urlencode(params)}"

def send_confirmation_email(user, booking):
    subject = "სერვისის ჯავშნის დასტური"
    recipient_email = user.email

    html_message = render_to_string("email_templates/booking_confirmation.html", {
        "user": user,
        "booking": booking,
        "google_calendar_link": generate_google_calendar_link(booking)
    })

    ics_content = generate_ics_file(booking, user)
    ics_filename = f"appointment_{booking.id}.ics"

    email = EmailMessage(
        subject,
        html_message,
        settings.EMAIL_HOST_USER,
        [recipient_email]
    )
    email.content_subtype = "html"
    email.attach(ics_filename, ics_content, "text/calendar")
    
    email.send()

    if "consultation" in booking.service.lower():
        fablab_email = "fablab@iliauni.edu.ge"
        fablab_email_msg = EmailMessage(
            subject,
            html_message,
            settings.EMAIL_HOST_USER,
            [fablab_email]
        )
        fablab_email_msg.content_subtype = "html"
        fablab_email_msg.attach(ics_filename, ics_content, "text/calendar")
        fablab_email_msg.send()


def send_cancelation_email(user):
    subject = "ვიზიტის ჯავშანი გაუქმებულია"
    recipient_email = user.email

    html_message = render_to_string("email_templates/booking_cancelation.html", {
        "user": user,
    })

    send_mail(
        subject,
        "",  
        settings.EMAIL_HOST_USER,
        [recipient_email],
        fail_silently=False,
        html_message=html_message,  
    )


def new_user_mail(user):
    subject = "რეგისტრაციის დასტური"
    recipient_email = user.email

    html_message = render_to_string("email_templates/new_user.html", {
        "user": user,
    })

    send_mail(
        subject,
        "",  
        settings.EMAIL_HOST_USER,
        [recipient_email],
        fail_silently=False,
        html_message=html_message,  
    )



@login_required
def cnc(request):
    if "language" in request.GET:
        language = request.GET["language"]
        if language in ["ka", "en"]:  # Allowed languages
            request.session["language"] = language  # Store in session
            activate(language)  # Change language immediately
        return redirect("cnc")  # Redirect to apply changes

    language = request.session.get("language", "ka")
    context = {"language": language}
    return render(request, 'cnc.html',context)



@login_required
def printing(request):

    if "language" in request.GET:
        language = request.GET["language"]
        if language in ["ka", "en"]:
            request.session["language"] = language 
            activate(language) 
        return redirect("3d_printing")  

    language = request.session.get("language", "ka")
    context = {"language": language}
    return render(request, '3d_printing.html',context)



def generate_meeting_ics_file(booking, user):
    """
    Generate an ICS file for the online consultation meeting.
    """
    cal = icalendar.Calendar()
    cal.add('prodid', '-//Fablab Iliauni//Online Consultation//EN')
    cal.add('version', '2.0')
    cal.add('method', 'REQUEST')

    event = icalendar.Event()
    event.add('summary', "ფაბლაბის ონლაინ კონსულტაცია")
    event.add('dtstart', datetime.combine(booking.date, booking.time))
    event.add('dtend', datetime.combine(booking.date, booking.time) + timedelta(minutes=booking.duration if hasattr(booking, "duration") else 60))
    event.add('dtstamp', datetime.now())
    event.add('location', booking.meeting_link)
    event.add('description', f"ეს არის ფაბლაბის ონლაინ კონსულტაცია. შეხვედრის ლინკი: {booking.meeting_link}")

    # Organizer (Fablab)
    organizer_email = "fablab@iliauni.edu.ge"
    event.add('organizer', f"MAILTO:{organizer_email}")

    # Attendees
    event.add('attendee', f"MAILTO:{user.email}", {"RSVP": "TRUE"})
    event.add('attendee', f"MAILTO:{organizer_email}", {"RSVP": "TRUE"})

    cal.add_component(event)
    return cal.to_ical()

def send_meeting_email(user, booking):
    """
    Send an email for an online consultation meeting with an ICS file.
    """
    subject = "ფაბლაბში ონლაინ კონსულტაცია"
    recipient_email = user.email

    html_message = render_to_string("email_templates/consultation_meeting.html", {
        "user": user,
        "booking": booking,
        "meeting_link": booking.meeting_link
    })

    # Generate ICS file
    ics_content = generate_meeting_ics_file(booking, user)
    ics_filename = f"online_meeting_{booking.id}.ics"

    # Send email with ICS attachment
    email = EmailMessage(
        subject,
        html_message,
        settings.EMAIL_HOST_USER,
        [recipient_email]
    )
    email.content_subtype = "html"  
    email.attach(ics_filename, ics_content, "text/calendar")  

    email.send()



# google meet generate

json_path = os.path.join(settings.BASE_DIR, 'appointment_app', 'data', 'credentials.json')

SCOPES = ["https://www.googleapis.com/auth/calendar.events"]

def authenticate_google():
    """
    Authenticate with Google using OAuth 2.0.
    Saves a token to avoid repeated logins.
    """
    creds = None

    if os.path.exists("token.pickle"):
        with open("token.pickle", "rb") as token:
            creds = pickle.load(token)


    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file(json_path, SCOPES)
        creds = flow.run_local_server(port=0)


        with open("token.pickle", "wb") as token:
            pickle.dump(creds, token)

    return build("calendar", "v3", credentials=creds)

def create_google_meet_link(booking):
    """
    Creates a Google Calendar event with a Google Meet link.
    """
    service = authenticate_google()


    tbilisi_tz = pytz.timezone("Asia/Tbilisi")
    utc_tz = pytz.utc

    # Convert booking time to Tbilisi timezone
    start_datetime = datetime.combine(booking.date, booking.time)
    start_datetime = tbilisi_tz.localize(start_datetime) 

    # Convert Tbilisi time to UTC
    start_datetime_utc = start_datetime.astimezone(utc_tz)
    end_datetime_utc = start_datetime_utc + timedelta(minutes=20)
    
    event = {
        "summary": f"{booking.service_type}",
        "description": f"{booking.service_type}",
        "start": {
            "dateTime": start_datetime_utc.isoformat(),
            "timeZone": "GMT-4",
        },
        "end": {
            "dateTime": end_datetime_utc.isoformat(),
            "timeZone": "GMT-4",
        },
        "conferenceData": {
            "createRequest": {
                "requestId": "python-meeting",
                "conferenceSolutionKey": {"type": "hangoutsMeet"},
            }
        },

    }

    # Create event in the primary calendar
    event_result = service.events().insert(
        calendarId="primary",
        body=event,
        conferenceDataVersion=1
    ).execute()

    meet_link = event_result.get("hangoutLink")
    return meet_link



# --------------- calendar add--------------
SERVICE_ACCOUNT_FILE = os.path.join(settings.BASE_DIR, 'appointment_app', 'data', 'cal-add.json')
SCOPES = ['https://www.googleapis.com/auth/calendar']
def get_calendar_service():
    """Authenticate and return the Google Calendar service instance."""
    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES
    )
    return build("calendar", "v3", credentials=credentials)


credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES
)

service = build('calendar', 'v3', credentials=credentials)

def add_event(booking, duration_minutes,topic):
    """
    Adds an event to Google Calendar with a specific duration.

    :param summary: Title of the event
    :param start_time: Start time of the event (timezone-aware datetime object)
    :param duration_minutes: Duration of the event in minutes
    """
    tbilisi_tz = pytz.timezone("Asia/Tbilisi")
    utc_tz = pytz.utc

    start_datetime = datetime.combine(booking.date, booking.time)

    if start_datetime.tzinfo is None: 
        start_datetime = tbilisi_tz.localize(start_datetime)

    start_datetime_utc = start_datetime.astimezone(utc_tz)
    end_datetime_utc = start_datetime_utc + timedelta(minutes=duration_minutes)

    event = {
        'summary': f"{topic} - {booking.user.first_name} {booking.user.last_name}",
        'start': {'dateTime': start_datetime_utc.isoformat(), 'timeZone': 'UTC'},
        'end': {'dateTime': end_datetime_utc.isoformat(), 'timeZone': 'UTC'},
    }

    event_result = service.events().insert(calendarId='fablab@iliauni.edu.ge', body=event).execute()
    print(f"Event created: {event_result.get('htmlLink')}")
    return event_result.get('id')


def delete_calendar_event(event_id):
    """Delete a Google Calendar event by ID."""
    if not event_id:
        return False  # No event to delete

    service = get_calendar_service()
    try:
        service.events().delete(calendarId="fablab@iliauni.edu.ge", eventId=event_id).execute()
        return True
    except Exception as e:
        print(f"Error deleting event: {e}")
        return False





# -------------------- reminder ---------------------


def check_and_send_reminders():
    """Manually check bookings and send email reminders for report submission."""

    today = now().date()  # Get current date

    # First Reminder: For bookings done 1 day ago
    first_reminder_bookings = Booking.objects.filter(
        date=today - timedelta(days=1), 
        report_submitted=False, 
        report_reminder_sent=False
    )

    for booking in first_reminder_bookings:
        send_report_reminder_email(booking)
        booking.report_reminder_sent = True
        booking.save()

    # ✅ Fixed: Second Reminder - More flexible query
    second_reminder_bookings = Booking.objects.filter(
        date__lte=today - timedelta(days=4),  # Booking is at least 4 days old
        report_submitted=False, 
        report_reminder_sent=True,  # First reminder was sent
        final_reminder_sent=False  # Final reminder not sent yet
    )

    for booking in second_reminder_bookings:
        send_final_reminder_email(booking)
        booking.final_reminder_sent = True
        booking.save()

    # ✅ Fixed: Deactivation Query
    deactivate_users = Booking.objects.filter(
        date__lte=today - timedelta(days=7),  # Booking is at least 7 days old
        report_submitted=False, 
        final_reminder_sent=True
    ).select_related('user')  # Get related user data

    for booking in deactivate_users:
        user = booking.user
        user.is_deactivated = True
        user.save()



def send_report_reminder_email(booking):
    """Send the first email reminder to submit the report."""
    subject = "ფაბლაბის ვიზიტის შესახებ უკუკავშირის შევსება"
    recipient_email = booking.user.email

    html_message = render_to_string("email_templates/report_reminder.html", {
        "user": booking.user,
        "booking": booking,
    })

    send_mail(
        subject,
        "",  
        settings.EMAIL_HOST_USER,
        [recipient_email],
        fail_silently=False,
        html_message=html_message,
    )


def send_final_reminder_email(booking):
    """Send the second and final email reminder to submit the report."""
    subject = "საყურადღებო-ფაბლაბის ვიზიტის შესახებ უკუკავშირის შევსება"
    recipient_email = booking.user.email

    html_message = render_to_string("email_templates/final_reminder.html", {
        "user": booking.user,
        "booking": booking,
    })

    send_mail(
        subject,
        "",  
        settings.EMAIL_HOST_USER,
        [recipient_email],
        fail_silently=False,
        html_message=html_message,
    )


def reach_limit_page(request):
    return render(request,"outoff_limit.html")