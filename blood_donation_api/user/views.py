import json
import requests

from django.contrib import messages
from django.contrib.auth import authenticate 
from django.contrib.auth import login, logout 
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse as JSONResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

from .forms import form_register, form_login, form_address, form_blood_group
from .models import blood_group, address, user_verification
from .models import user as user_model

from blood_donation_api import utilities
from blood_donation_api.utilities import messages_as_json, form_errors_as_json, user_record_to_json
from blood_donation_api.settings import FIREBASE_CONFIG

from firebase_admin import auth, firestore
db = firestore.client()

@csrf_exempt
def get_csrf(request):
    if request.method == "POST":
        rendered_html = render(request, 'user/form.html', {"context": True})
        csrf_token = request.COOKIES.get('csrftoken')
        messages.info(request, f"Request successful")
        return JSONResponse({"status":True, "messages": messages_as_json(request), "data": csrf_token}, status=200)
    else:
        messages.error(request, f"Invalid request")
        return JSONResponse({"status":False, "messages": messages_as_json(request)}, status=405)
        
def getuser(request, username, mode='get'):
    """
    Args:
    :param mode (optional): 
        - 'get'     : mode to get users via their email, phone or username.
        - 'check'   : mode to check if a user already exists via their email, phone or username.
    """
    user = None
    identifier = None

    if mode == 'get': 
        try:
            user = auth.get_user(username)
            identifier = 'username'
        except:
            if user is None:
                try:
                    user = auth.get_user_by_email(username)
                    identifier = 'email'
                except:
                    pass
        return user

    if mode == 'check':
        try:
            user = auth.get_user(username['username'])
            identifier = 'username'
        except:
            if user is None:
                try:
                    user = auth.get_user_by_email(username['email'])
                    identifier = 'email'
                except:
                    # user = auth.get_user_by_phone_number(phone)
                    # identifier = 'phone'
                    pass
        if user is not None:
            return [True, identifier]
        else:
            return [False, identifier]

@csrf_exempt
def user_login(request):
    if request.method == "POST":
        form = form_login(request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = getuser(request, username, 'get')
            if user is not None:
                username = user.uid
                request_ref = "https://www.googleapis.com/identitytoolkit/v3/relyingparty/verifyPassword?key={0}".format(FIREBASE_CONFIG['apiKey'])
                headers = {"content-type": "application/json; charset=UTF-8"}
                data = json.dumps({"email": user.email, "password": password, "returnSecureToken": True})
                request_object = requests.post(request_ref, headers=headers, data=data)

                try:
                    request_object.raise_for_status()
                    user_record = request_object.json()

                    if(user_record['idToken'] is None or (user_record['registered'] == False)):
                        raise Exception('User not authenticated or properly registered')

                    data = {
                        "idToken": user_record['idToken'],
                        "refreshToken": user_record['refreshToken'],
                        "expiresIn": user_record['expiresIn'],
                        "username": username,
                        "user": user_record_to_json(user)
                    }

                    user_local, created = user_model.objects.get_or_create(username=username, password=password)
                    authenticate_return = authenticate(username=username, password=password)
                    request.user = user_local
                    login(request, user_local)
                    messages.success(request, f"You are logged in as: {username}")
                    return JSONResponse({"status":True, "messages": messages_as_json(request), "data": data}, status=200)   
                except Exception as e:
                    # TODO: Check if we get a { "error" : "Permission denied." } and handle automatically
                    # TODO: Check if we get a { "error" : "Authenticate Error" } and handle
                    messages.error(request, "Invalid username or password. Authentication Error.")
                    return JSONResponse({"status":False, "messages": messages_as_json(request), "errors": str(e)}, status=401)         
            else:
                messages.error(request, f"Invalid username or password")
                return JSONResponse({"status":False, "messages": messages_as_json(request)}, status=401)
        else:
            messages.error(request, f"Invalid input")
            return JSONResponse({"status":False, "messages": messages_as_json(request), "errors": form_errors_as_json(form)}, status=400)
    else:
        messages.error(request, f"Invalid request")
        return JSONResponse({"status":False, "messages": messages_as_json(request)}, status=405)

@login_required
def user_logout(request):
    logout(request)
    messages.info(request, f"You are logged out")
    return JSONResponse({"status":True, "messages": messages_as_json(request)}, status=200)


def user_register(request):
    if request.method == "POST":
        form = form_register(request.POST)
        if form.is_valid():
            user_exists = getuser(request, {'username': form.cleaned_data.get('username'), 'email': form.cleaned_data.get('email')}, 'check')
            if user_exists[0]:
                messages.error(request, f"A User with that {user_exists[1]} already exists")
                return JSONResponse({"status":False, "messages": messages_as_json(request)}, status=403)
            else:
                new_user = auth.create_user(
                    uid = form.cleaned_data.get('username'),
                    email = form.cleaned_data.get('email'),
                    email_verified = False,
                    phone_number = form.cleaned_data.get('phone'),
                    password = form.cleaned_data.get('password'),
                    display_name = form.cleaned_data.get('display_name'),
                    disabled = False
                )
                messages.success(request, f"User \'{new_user.uid}\' created successfully")
                return JSONResponse({"status":True, "messages": messages_as_json(request)}, status=201)
        else:
            form_errors_as_json(form)
            messages.error(request, f"Invalid input")
            return JSONResponse({"status":False, "messages": messages_as_json(request), "errors": form_errors_as_json(form)}, status=400)
    else:
        messages.error(request, f"Invalid request")
        return JSONResponse({"status":False, "messages": messages_as_json(request)}, status=405)

# @login_required


def getaddress(request):
    

            
    return JSONResponse({"status":True}, status=200)

def putaddress(request):
    location_info_Nepal = utilities.location_info_Nepal()
    for state in location_info_Nepal['provinceList']:
        for district in state['districtList']:
            for municipality in district['municipalityList']:
                doc_ref = db.collection("address").document("Nepal").collection((state['name']).title()).document(district['name']).collection(municipality['name']).document("Cities")
                doc_ref.set({"City": "Test 1"})
    return JSONResponse({"status":True}, status=200)

def putuseraddress(request):
    if(request.method == "POST"):
        form = form_address(response.POST)
        if form.is_valid():
            blood_data = form.save()
            messages.info(request, f"New address registered")
            return JSONResponse({"status":True, "messages": messages_as_json(request)}, status=200)
        else:
            messages.error(request, f"Invalid data")
            return JSONResponse({"status":False, "messages": messages_as_json(request)}, status=400)

def getbloodgroup(request):
    users_ref = db.collection("blood_group")
    docs = users_ref.stream()
    data = {}
    for doc in docs:
        data[doc.id] = doc.to_dict()
    messages.success(request, f"Successfully retrieved blood group data")
    return JSONResponse({"status":True, "data": data, "messages": messages_as_json(request)}, status=200)

def putbloodgroup(request):
    try:
        doc_ref = db.collection("blood_group").document("A+")
        doc_ref.set({"blood_group_name": "A Positive", "description": "A RhD Positive (A+)", "matching_doners": "A+, A-, O+, O-"})
        doc_ref = db.collection("blood_group").document("A-")
        doc_ref.set({"blood_group_name": "A Negative", "description": "A RhD Negative (A-)", "matching_doners": "A-, O-"})
        doc_ref = db.collection("blood_group").document("B+")
        doc_ref.set({"blood_group_name": "B Positive", "description": "B RhD Positive (B+)", "matching_doners": "B+, B-, O+, O-"})
        doc_ref = db.collection("blood_group").document("B-")
        doc_ref.set({"blood_group_name": "B Negative", "description": "B RhD Negative (B-)", "matching_doners": "B-, O-"})
        doc_ref = db.collection("blood_group").document("AB+")
        doc_ref.set({"blood_group_name": "AB Positive", "description": "AB RhD Positive (AB+)", "matching_doners": "A+, A-, B+, B-, O+, O-, AB+, AB-"})
        doc_ref = db.collection("blood_group").document("AB-")
        doc_ref.set({"blood_group_name": "AB Negative", "description": "AB RhD Negative (AB-)", "matching_doners": "AB-, A-, B-, O-"})
        doc_ref = db.collection("blood_group").document("O+")
        doc_ref.set({"blood_group_name": "O Positive", "description": "O RhD Positive (O+)", "matching_doners": "O+, O-"})
        doc_ref = db.collection("blood_group").document("O-")
        doc_ref.set({"blood_group_name": "O Negative", "description": "O RhD Negative (O-)", "matching_doners": "O-"})
        messages.success(request, f"Successfully added blood group")
        return JSONResponse({"status":True,"messages": messages_as_json(request)}, status=200)
    except:
        messages.error(request, f"Internal Server Error")
        return JSONResponse({"status":False,"messages": messages_as_json(request)}, status=500)