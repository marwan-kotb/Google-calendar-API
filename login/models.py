from email.policy import default
from enum import unique
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models.deletion import CASCADE
from django.db.models.fields import related
from address.models import AddressField

class User(AbstractUser):
    img = models.ImageField(upload_to='imagesProfile/')
    address = AddressField(related_name='+', blank=True)
    is_patient = models.BooleanField(null=True)


class Category(models.Model):
    categryName = models.CharField(blank=True, max_length=64, unique=True)


class Blogs(models.Model):
    
    writer = models.ForeignKey(User, on_delete=models.CASCADE, related_name="user")
    title = models.CharField(blank=True, max_length=64)
    imgBlog = models.ImageField(upload_to='imagesBlogs/')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="blog")
    summary = models.TextField(blank=True, max_length=16)
    content = models.TextField(verbose_name=("details"), blank=True)
    drafted = models.BooleanField(default=False)


class Appointments(models.Model):

    doctor = models.ForeignKey(User, on_delete=models.CASCADE, related_name="doctor")
    patient = models.ForeignKey(User, on_delete=models.CASCADE, related_name="patient")
    dateTime = models.DateTimeField()
    speciality = models.CharField(blank=True, null=True, max_length=50)




