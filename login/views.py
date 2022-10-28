from re import A
from sre_parse import CATEGORIES
from typing import final
from unicodedata import category
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.contrib.auth.decorators import login_required
import pytz
from .models import *
import datetime
from datetime import timedelta, datetime

import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/calendar.events']



def Data(request):
    user=request.user
    
    if request.user.is_patient:
        
        data = Blogs.objects.filter(drafted=False)
      
    else:
        data = Blogs.objects.filter(writer=user)
    
    return data

def index(request):
    return render(request, "login/index.html")


@csrf_exempt
def login_view(request):
    
    doctors = User.objects.filter(is_patient=False)

    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)
        
        # Check if authentication successful
        if user is not None:
            login(request, user)
            return render(request, "login/index.html", {
                "user": user, "data":Data(request), "doctors":doctors
            })
        else:
            return render(request, "login/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "login/login.html")

def logout_view(request):
    logout(request)
    return render(request, "login/index.html")


@csrf_exempt
def register(request, type):
    
    is_patient = False
    if type == 'Patient':
        is_patient = True

    if request.method == "POST":
        try:
            img = request.FILES['img']
        except:
            return render(request, "login/register.html", {
                "message": "Upload Picture."
            })

        firstname = request.POST['firstname']
        lastname = request.POST['lastname']
        # img = request.FILES['img'] 
        username = request.POST["username"]
        email = request.POST["email"]
        address = request.POST['address']
        
        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "login/register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=firstname,
                last_name=lastname,
                img=img,
                address=address,
                is_patient=is_patient
            )
            user.save()
        
        except:
            return render(request, "login/register.html", {
                "message": "Username already taken."
            })
        
        return render(request, "login/login.html")
    else:
        return render(request, "login/register.html")

@login_required
@csrf_exempt
def blogs(request):

    writer = request.user
    data = Data(request)
    categories = Category.objects.all()

    if request.method == "POST":

        try:
            title = request.POST['title']
            imgBlog = request.FILES['imgBlog']
            category = request.POST['categ']
            summary = request.POST['summary']
            content = request.POST['content']
            
        
        except:
            return render(request, "login/blogs.html", {
                "message": "Fill in all the data.", "categories":categories
            })

        try:
            drafted = request.POST['drafted']
        except:
            drafted = 'False'
        temp = summary.split()
        if len(temp) > 15:
            temp = temp[:14]
            temp.append('...')
            summary = ' '.join(temp)
        category = Category.objects.get(id=category)
        if drafted == 'True':
            drafted = True
        else:
            drafted = False
        
        try:
            blog = Blogs.objects.create(
                writer=writer,
                title=title,
                imgBlog=imgBlog,
                category=category,
                summary=summary,
                content=content,
                drafted=drafted
            )
            blog.save()
            return render(request, "login/index.html", {
                "user":writer, "data":data, "doctors":User.objects.filter(is_patient=False)
            })
        except:
            return render(request, "login/blogs.html", {
                "message": "Try Again.", "categories":categories
            })
    
    return render(request, "login/blogs.html", {
                "user" : writer, "categories" : categories
            })


@login_required
@csrf_exempt
def Book(request, doc, pat):

    DATE_INPUT_FORMATS = "%Y-%m-%dT%H:%M"

    if request.method == "POST":
        
        try:
        
            appointment = request.POST['appointment']
            speciality = request.POST['speciality']
            
        except:
            return render(request, "login/Book.html", {
                "message": "Try Again.", "doc":doc, "pat":pat
            })
        
        parsed_date = datetime.strptime(appointment, DATE_INPUT_FORMATS)
        cairo_timezone = pytz.timezone('Africa/Cairo')
        date_search = cairo_timezone.localize(parsed_date)
        
        try:
            if (Appointments.objects.filter(dateTime=date_search)):
                return render(request, "login/Book.html", {
                    "message": "The Appointment Already Taken.", "doc":doc, "pat":pat
                })
        except:
            pass
        

        final_time = date_search + timedelta(minutes=45)
        
        try:
            
            
            A = Appointments.objects.create(
                doctor=User.objects.get(username=doc),
                patient=User.objects.get(username=pat),
                dateTime=date_search,
                speciality=speciality
            )

            
            creds = None

            if os.path.exists('token.json'):
                creds = Credentials.from_authorized_user_file('token.json', SCOPES)
            # If there are no (valid) credentials available, let the user log in.
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        'credentials.json', SCOPES)
                    creds = flow.run_local_server(port=0)
                # Save the credentials for the next run
                with open('token.json', 'w') as token:
                    token.write(creds.to_json())

           
            service = build('calendar', 'v3', credentials=creds)

            event = {
            
            'description': speciality,
            'end': {
                'dateTime': 'T'.join(str(final_time).split()),
                'timeZone': 'Africa/Cairo',
            },
            'start': {
                'dateTime': 'T'.join(str(date_search).split()),
                'timeZone': 'Africa/Cairo',
            },
        }

            event = service.events().insert(calendarId='primary', body=event).execute()   
            A.save()

            return render(request, 'login/saving.html', {
                "doctor":doc, "date":appointment[:10], "starttime":appointment[11:], "endtime":(str(final_time)[11:16]),
                "event":event['htmlLink']
            })
        except:
            return render(request, "login/Book.html", {
                "message": "Try Again event didn't be saved", "doc":doc, "pat":pat
            })

    return render(request, 'login/Book.html', {
        "doc":doc, "pat":pat
    })










