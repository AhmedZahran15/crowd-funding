from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator

# Create your models here.

class User(AbstractUser):
    email = models.EmailField(unique=True)
    mobile_phone = models.CharField(
        max_length=11,
        validators=[RegexValidator(regex=r'^01[0125][0-9]{8}$', message="Invalid Egyptian phone number")]
    )
    profile_picture = models.ImageField(upload_to='profiles/', null=True, blank=True)
    birthdate = models.DateField(null=True, blank=True)
    facebook_profile = models.URLField(null=True, blank=True)
    country = models.CharField(max_length=100, null=True, blank=True)
    is_active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.email