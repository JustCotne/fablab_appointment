from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser, Booking


FACULTY_CHOICES = [
    ('მეცნიერებათა და ხელოვნების ფაკულტეტი', 'მეცნიერებათა და ხელოვნების ფაკულტეტი'),
    ('საბუნებისმეტყველო მეცნიერებებისა და მედიცინის ფაკულტეტი', 'საბუნებისმეტყველო მეცნიერებებისა და მედიცინის ფაკულტეტი'),
    ('ბიზნესის, ტექნოლოგიისა და განათლების ფაკულტეტი', 'ბიზნესის, ტექნოლოგიისა და განათლების ფაკულტეტი'),
    ('სამართლის სკოლა', 'სამართლის სკოლა'),
]

class CreateUserForm(UserCreationForm):
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    phone_number = forms.CharField(max_length=13, required=True, label="Phone Number") 
    email = forms.EmailField(required=True)
    faculty = forms.ChoiceField(choices=FACULTY_CHOICES, required=True, label="Faculty")
    program = forms.CharField(max_length=100, required=True, label="Program")

    class Meta:
        model = CustomUser  # Use CustomUser instead of User
        fields = ['first_name', 'last_name', 'phone_number', 'email', 'faculty', 'program', 'password1', 'password2']

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if CustomUser.objects.filter(email=email).exists():
            raise forms.ValidationError("A user with this email already exists.")
        if not email.endswith('@iliauni.edu.ge'):
            raise forms.ValidationError("Email must be from iliauni.edu.ge domain")
        return email


    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = self.cleaned_data.get('email')
        if commit:
            user.save()
        return user


class LaserBookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ["first_name", "last_name", "phone_number", "email", "service", "date", "time", "project_details", "file"]

class ConsultationBookingForm(forms.ModelForm):
    MEETING_TYPE_CHOICES = [
        ('offline', 'Offline'),
        ('online', 'Online'),
    ]
    SERVICE_TYPE_CHOICES = [
        ('სტარტაპ კონსულტაცია/Startup Consultation', 'სტარტაპ კონსულტაცია/Startup Consultation'),
        ('საგრანტო კონსულტაცია/Grant Consultation', 'საგრანტო კონსულტაცია/Grant Consultation'),
        ('საინჟინრო კონსულტაცია/Engineering consultation', 'საინჟინრო კონსულტაცია/Engineering consultation'),
        ('პროგრამული კონსულტაცია/Software consultation', 'პროგრამული კონსულტაცია/Software consultation'),
        ('იდეის დამუშავება/Working on the idea', 'იდეის დამუშავება/Working on the idea'),
        ('3D პრინტერის პროექტზე კონსულტაცია/Consultation for 3D printer project', '3D პრინტერის პროექტზე კონსულტაცია/Consultation for 3D printer project'),
        ('ლაზერული მჭრელის პროექტზე კონსულტაცია/Consultation for laser cutter machine project', 'ლაზერული მჭრელის პროექტზე კონსულტაცია/Consultation for laser cutter machine project'),
        ('CNC პროგრამირებადი ჩარხის პროექტზე კონსულტაცია/Consultation for CNC machine project', 'CNC პროგრამირებადი ჩარხის პროექტზე კონსულტაცია/Consultation for CNC machine project'),
        ('სხვა/other','სხვა/other'),
    ]

    service_type = forms.ChoiceField(choices=SERVICE_TYPE_CHOICES, required=True, label="Service Type")
    meeting_type = forms.ChoiceField(choices=MEETING_TYPE_CHOICES, required=True, label="Meeting Type")

    class Meta:
        model = Booking
        fields = ["first_name", "last_name", "phone_number", "email", "service", "date", "time","service_type","project_details", "meeting_type"]
