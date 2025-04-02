from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings


FACULTY_CHOICES = [
    ('მეცნიერებათა და ხელოვნების ფაკულტეტი', 'მეცნიერებათა და ხელოვნების ფაკულტეტი'),
    ('საბუნებისმეტყველო მეცნიერებებისა და მედიცინის ფაკულტეტი', 'საბუნებისმეტყველო მეცნიერებებისა და მედიცინის ფაკულტეტი'),
    ('ბიზნესის, ტექნოლოგიისა და განათლების ფაკულტეტი', 'ბიზნესის, ტექნოლოგიისა და განათლების ფაკულტეტი'),
    ('სამართლის სკოლა', 'სამართლის სკოლა'),
]

class CustomUser(AbstractUser):
    phone_number = models.CharField(max_length=13, blank=True, null=True, verbose_name="Phone Number")
    faculty = models.CharField(max_length=255, choices=FACULTY_CHOICES, blank=True, null=True)
    program = models.CharField(max_length=255, blank=True, null=True)
    is_deactivated = models.BooleanField(default=False, verbose_name="Deactivate Account")
    booking_limit = models.IntegerField(default=3, verbose_name="Remaining Bookings")

    def __str__(self):
        return self.username

class UserProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    bio = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.user.username} Profile"


class Booking(models.Model):
    SERVICE_TYPE_CHOICES = [
        ('სტარტაპ კონსულტაცია/Startup Consultation', 'სტარტაპ კონსულტაცია/Startup Consultation'),
        ('საგრანტო კონსულტაცია/Grant Consultation', 'საგრანტო კონსულტაცია/Grant Consultation'),
        ('საინჟინრო კონსულტაცია/Engineering consultation', 'საინჟინრო კონსულტაცია/Engineering consultation'),
        ('პროგრამული კონსულტაცია/Software consultation', 'პროგრამული კონსულტაცია/Software consultation'),
        ('იდეის დამუშავება/Working on the idea', 'იდეის დამუშავება/Working on the idea'),
        ('3D პრინტერის პროექტზე კონსულტაცია/Consultation for 3D printer project', '3D პრინტერის პროექტზე კონსულტაცია/Consultation for 3D printer project'),
        ('ლაზერული მჭრელის პროექტზე კონსულტაცია/Consultation for laser cutter machine project', 'ლაზერული მჭრელის პროექტზე კონსულტაცია/Consultation for laser cutter machine project'),
        ('CNC პროგრამირებადი ჩარხის პროექტზე კონსულტაცია/Consultation for CNC machine project', 'CNC პროგრამირებადი ჩარხის პროექტზე კონსულტაცია/Consultation for CNC machine project'),
        ('სხვა/other', 'სხვა/other'),
    ]

    MEETING_TYPE_CHOICES = [
        ('online', 'Online'),
        ('offline', 'Offline'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=30, blank=True, null=True)  
    last_name = models.CharField(max_length=30, blank=True, null=True) 
    phone_number = models.CharField(max_length=13, blank=True, null=True) 
    email = models.EmailField(blank=True, null=True) 
    service = models.CharField(max_length=50)
    service_type = models.CharField(max_length=255, choices=SERVICE_TYPE_CHOICES, blank=True, null=True)
    meeting_type = models.CharField(max_length=20, choices=MEETING_TYPE_CHOICES, blank=True, null=True)
    date = models.DateField()
    time = models.TimeField()
    project_details = models.TextField(blank=True, null=True)
    file = models.FileField(upload_to='uploads/', blank=True, null=True)
    meeting_link = models.URLField(blank=True, null=True)

    report_submitted = models.BooleanField(default=False)
    report_reminder_sent = models.BooleanField(default=False)  
    final_reminder_sent = models.BooleanField(default=False)

    google_calendar_event_id = models.CharField(max_length=255, blank=True, null=True) 

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name} - {self.service} - {self.date} {self.time}"