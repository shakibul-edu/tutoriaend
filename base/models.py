from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.contrib.gis.db import models as geomodels
from django.db.models import CheckConstraint, Q
 

class CustomUser(AbstractUser):
    is_teacher = models.BooleanField(default=False)
    location = geomodels.PointField(null=True, blank=True,geography=True, help_text="The geographical location of the user.")
    banned = models.BooleanField(default=False, help_text="Indicates if the user is banned from the platform.")

def certificate_upload_to(instance, filename):
    return f"certificates/{instance.teacher.user.username}/{instance.degree if type(instance)==AcademicProfile else instance.skill}/{filename}"

class Medium(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


    
class Grade(models.Model):
    medium = models.ManyToManyField(Medium, blank=True, related_name='mediums')
    name = models.CharField(max_length=50, unique=True, help_text="The name of the grade (e.g., '10th', '12th ')")
    sequence = models.PositiveIntegerField(unique=True, help_text="The sequence number of the grade (e.g., 10 for '10th Grade', 12 for '12th Grade')")

    def __str__(self):
        return self.name
    
class Subject(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True, help_text="A brief description of the subject.")
    subject_code = models.CharField(max_length=20, unique=True, help_text="A unique code for the subject (e.g., 'MATH101', 'PHY202')", blank=True, null=True)
    grade = models.ForeignKey(Grade, on_delete=models.CASCADE, related_name='subjects', blank=True, null=True, help_text="The grade level for which this subject is applicable.")
    def __str__(self):
        return self.name

class AcademicProfile(models.Model):
    teacher = models.ForeignKey('TeacherProfile', on_delete=models.CASCADE, related_name='academic_profile')
    institution = models.CharField(max_length=25)
    degree = models.CharField(max_length=100)
    graduation_year = models.PositiveIntegerField()
    results = models.TextField(blank=True)
    certificates = models.FileField(upload_to=certificate_upload_to, blank=True, null=True)
    validated = models.BooleanField(default=False, help_text="Indicates if the academic profile has been validated by an admin.")

    def __str__(self):
        return f"{self.teacher.user.username}'s Academic Profile"
    
    def delete(self, *args, **kwargs):
        """
        Deletes the file from the filesystem before deleting the model instance.
        """
        self.certificates.delete(save=False)  # Delete the file first
        super().delete(*args, **kwargs) 
    

    
class Qualification(models.Model):
    teacher = models.ForeignKey('TeacherProfile', on_delete=models.CASCADE, related_name='qualifications')
    organization = models.CharField(max_length=255, blank=True)
    skill = models.CharField(max_length=100)
    year = models.PositiveIntegerField(null=True, blank=True)
    results = models.TextField(blank=True,null=True)
    certificates = models.FileField(upload_to=certificate_upload_to, blank=True, null=True)
    validated = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.teacher.user.username}'s Academic Profile"
    
    def delete(self, *args, **kwargs):
        """
        Deletes the file from the filesystem before deleting the model instance.
        """
        self.certificates.delete(save=False)  # Delete the file first
        super().delete(*args, **kwargs)  

class TeacherProfile(models.Model):
    user = models.OneToOneField('CustomUser', on_delete=models.CASCADE, related_name='teacher_profile')
    verified = models.BooleanField(default=False, help_text="Indicates if the teacher's profile has been verified by an admin.")
    bio = models.TextField(blank=True, null=True, help_text="A brief biography of the teacher.")
    subject_list = models.ManyToManyField(
        Subject,
        related_name='tutors', # Allows accessing tutors from a subject object (e.g., subject.tutors.all())
        blank=True, # Tutors are not required to have subjects initially
        help_text="The subjects this tutor can teach."
    )
    grade_list = models.ManyToManyField(
        Grade,
        related_name='tutors', # Allows accessing tutors from a grade object (e.g., grade.tutors.all())
        blank=True, # Tutors are not required to have grades initially
        help_text="The grades this tutor can teach."
    )
    min_salary = models.PositiveIntegerField(default=0)
    experience_years = models.PositiveIntegerField(default=0)
    medium = models.ManyToManyField(Medium, blank=True, related_name='teacher_profiles')
    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
        ('any', 'Any'),
    ]

    TEACHING_CHOICES = [
        ('online', 'Online'),
        ('in_person', 'In Person'),
        ('batch_online', 'Batch Online'),
        ('batch_in_person', 'Batch In Person'),
        ('both', 'Both'),
    ]
    gender = models.CharField(max_length=20, choices=GENDER_CHOICES, blank=True)
    teaching_mode = models.CharField(max_length=20, choices=TEACHING_CHOICES, blank=True)
    preferred_distance = models.PositiveIntegerField(default=0, help_text="Preferred distance for teaching in kilometers")

    def __str__(self):
        return f"{self.user.username}'s Teacher Profile"

    def clean(self):
        # Ensure the associated user has a location set
        if not self.user.location:
            raise ValidationError(
            {'user': _('User must update their location before creating a teacher profile.')}
            )


class Availability(models.Model):
    """
    Represents a specific time slot a tutor is available on a given day.
    A tutor can have multiple availability slots on the same day.
    """
    DAY_CHOICES = [
        ('MON', 'Monday'),
        ('TUE', 'Tuesday'),
        ('WED', 'Wednesday'),
        ('THU', 'Thursday'),
        ('FRI', 'Friday'),
        ('SAT', 'Saturday'),
        ('SUN', 'Sunday'),
    ]

    tutor = models.ForeignKey(
        TeacherProfile,
        on_delete=models.CASCADE, # If a tutor is deleted, their availabilities are also deleted.
        related_name='availabilities', # Allows accessing availabilities from a tutor object (e.g., tutor.availabilities.all())
        help_text="The tutor associated with this availability slot."
    )
    start_time = models.TimeField(help_text="The start time of the availability slot.")
    end_time = models.TimeField(help_text="The end time of the availability slot.")
    days_of_week = models.CharField(max_length=3, choices=DAY_CHOICES, help_text="The day of the week for this availability slot.")




    class Meta:
        verbose_name = "Availability Slot"
        verbose_name_plural = "Availability Slots"
        # Ensure that a tutor cannot have overlapping time slots on the same day.
        # This unique_together constraint helps prevent simple overlaps,
        # but more complex overlap logic might be needed in clean method or forms.
        unique_together = ('tutor',  'start_time', 'end_time')
        ordering = ['tutor__user__username',  'start_time'] # Order by tutor, then day, then start time.

    def clean(self):
        """
        Custom validation to ensure end_time is after start_time.
        """
        if self.start_time and self.end_time:
            if self.start_time >= self.end_time:
                raise ValidationError(
                    _('End time must be after start time.'),
                    code='invalid_time_range'
                )

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.tutor.user.username} - ({self.start_time.strftime('%I:%M %p')} - {self.end_time.strftime('%I:%M %p')})"
