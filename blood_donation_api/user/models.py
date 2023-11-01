from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import UserManager
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.db import models
from django.utils import timezone

class address(models.Model):
    area = models.CharField(max_length=20, blank=True)
    city = models.CharField(max_length=20, blank=True)
    state = models.CharField(max_length=20, blank=True)
    zip = models.IntegerField(null=True, blank=True)
    country = models.CharField(max_length=20, null=False, blank=False)

class blood_group(models.Model):
    blood_group = models.CharField(max_length=5, blank=False) #id
    blood_group_name = models.CharField(max_length=20, blank=False)
    description = models.CharField(max_length=500, blank=False)
    matching_doners = models.ManyToManyField('self', blank=True)

class user(AbstractUser):
    # Django default fields in a AbstractUser class:
        # first_name 
        # last_name
        # username 
        # email
        # is_staff 
        # date_joined
    # Custom fields:
    phone_number = models.CharField(max_length=15, null=True, blank=True)
    gender = models.SmallIntegerField(null=True, blank=True)
    address_id = models.ForeignKey(address, null=True, blank=True, on_delete=models.SET_NULL)
    blood_group_id =  models.ForeignKey(blood_group, null=True, blank=True, on_delete=models.SET_NULL)


    # class Meta:
    #     abstract = True

class user_verification(models.Model):
    user_id = models.ForeignKey(user, on_delete=models.CASCADE)
    is_email_verified = models.BinaryField(default=False)
    is_phone_verified = models.BinaryField(default=False)

