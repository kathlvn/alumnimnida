from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.db import models

class CustomUserManager(BaseUserManager):
    def create_user(self, student_number, password=None, **extra_fields):
        if not student_number:
            raise ValueError("The Student Number is required.")
        user = self.model(student_number=student_number, **extra_fields)  # removed username
        user.set_password(password or student_number)
        user.save()
        return user

    def create_superuser(self, student_number, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(student_number, password, **extra_fields)

class CustomUser(AbstractBaseUser, PermissionsMixin):
    student_number = models.CharField(max_length=20, unique=True)
    email = models.EmailField(blank=True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    birthday = models.DateField(null=True, blank=True)
    address = models.CharField(max_length=255, blank=True)
    location = models.CharField(max_length=100, blank=True)
    degree = models.CharField(max_length=100, blank=True)
    year_attended = models.IntegerField(null=True, blank=True)
    year_graduated = models.IntegerField(null=True, blank=True)
    contact = models.CharField(max_length=20, blank=True)
    club_orgs = models.TextField(blank=True)
    professional_background = models.TextField(blank=True)

    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    USERNAME_FIELD = 'student_number'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    objects = CustomUserManager()

    def __str__(self):
        return self.student_number
