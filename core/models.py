from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.contrib.auth import get_user_model
from django.conf import settings
from django.db import models
from django.utils import timezone
import datetime

class CustomUserManager(BaseUserManager):
    
    def create_user(self, student_number=None, password=None, **extra_fields):
        if not student_number and not extra_fields.get('is_staff'):
            raise ValueError("Student number is required")
        
        user = self.model(student_number=student_number, **extra_fields)
        user.set_password(password or student_number)
        user.save()
        return user

    def create_superuser(self, student_number, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(student_number, password, **extra_fields)
    
    def create_admin(self, username, password, first_name, last_name, email='', **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', False)
        return self.create_user(username=username, password=password, student_number=username,
                                 first_name=first_name, last_name=last_name, email=email, **extra_fields)



class CustomUser(AbstractBaseUser, PermissionsMixin):
    id = models.AutoField(primary_key=True)
    student_number = models.CharField(max_length=20, unique=True, null=True, blank=True) #nulled for admin registration
    email = models.EmailField(blank=True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    birthday = models.DateField(null=True, blank=True)
    address = models.CharField(max_length=255, blank=True)
    curr_location = models.CharField(max_length=100, blank=True)

    degree_choices = [
        ('BSCS', 'BS Computer Science'),
        ('BSIT', 'BS Information Technology'),
        ('BSEMC', 'BS Entertainment and Multimedia Computing'),
        ('ACT', 'Associate in Computer Technology'),
    ]
    degree = models.CharField(max_length=100, choices=degree_choices, blank=True)
    current_year = datetime.datetime.now().year
    year_selection = [(year, str(year)) for year in range(current_year, 2015, -1)]  
    year_attended = models.IntegerField(choices=year_selection, null=True, blank=True)
    year_graduated = models.IntegerField(choices=year_selection, null=True, blank=True)
    
    contact = models.CharField(max_length=11, blank=True)
    club_orgs = models.TextField(blank=True)
    bio = models.TextField(blank=True)

    EMPLOYMENT_STATUS_CHOICES = [
        ('employed', 'Employed'),
        ('freelancing', 'Freelancing'),
        ('unemployed', 'Unemployed'),
        ('studying', 'Studying'),
        ('other', 'Other'),
    ]


    employment_status = models.CharField(max_length=20, choices=EMPLOYMENT_STATUS_CHOICES, blank=True, null=True)

    username = models.CharField(max_length=150, unique=True, null=True, blank=True) #for registry

    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    USERNAME_FIELD = 'student_number'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    objects = CustomUserManager()

    def __str__(self):
        return self.student_number or self.username or f"User {self.pk}"

    
    @property
    def program(self):
        return self.degree
    
    @property
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    @property
    def batch(self):
        return self.year_graduated
    
class JobEntry(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='job_entries')
    job_title = models.CharField(max_length=100)
    date_added = models.DateTimeField(auto_now_add=True)
    is_current = models.BooleanField(default=False)

    def __str__(self):
        return self.job_title
    

    
#ext functions
class Event(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    location = models.CharField(max_length=255)
    datetime = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    done = models.BooleanField(default=False)

    def __str__(self):
        return self.title
    


class Updates(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    date_posted = models.DateTimeField(auto_now_add=True)
    related_event = models.ForeignKey('Event', on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.title
    


class Forum(models.Model):
    title = models.CharField(max_length=255)
    content = models.TextField()
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    date_posted = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class Like(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    post = models.ForeignKey('Forum', on_delete=models.CASCADE, related_name='likes')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'post')

class Comment(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    post = models.ForeignKey('Forum', on_delete=models.CASCADE, related_name='comments')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)