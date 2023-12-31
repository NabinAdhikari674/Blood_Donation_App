import json
import requests
import math
from datetime import datetime

from django.contrib import messages
from django.contrib.auth import authenticate 
from django.contrib.auth import login, logout 
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse as JSONResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

from .forms import *
from .models import blood_group, address, user_verification
from .models import user as user_model

from blood_donation_api.utilities import *
# from blood_donation_api.utilities import messages_as_json, form_errors_as_json, user_record_to_json
from blood_donation_api.settings import FIREBASE_CONFIG

from firebase_admin import auth, firestore
from google.cloud.firestore_v1.base_query import FieldFilter

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

                    user_details = user_get_detail(user.uid)
                    data = {
                        "idToken": user_record['idToken'],
                        "refreshToken": user_record['refreshToken'],
                        "expiresIn": user_record['expiresIn'],
                        "username": username,
                        "user": user_record_to_json(user),
                        "user_details": user_details
                    }

                    user_local, created = user_model.objects.get_or_create(username=username, password=password)
                    authenticate_return = authenticate(username=username, password=password)
                    request.user = user_local
                    login(request, user_local)
                    messages.success(request, f"You are logged in as: {username}")
                    return JSONResponse({"status":True, "messages": messages_as_json(request), "data": data}, status=200)   
                except Exception as e:
                    print(e)
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
                try:
                    new_user = auth.create_user(
                        uid = form.cleaned_data.get('username'),
                        email = form.cleaned_data.get('email'),
                        email_verified = False,
                        phone_number = form.cleaned_data.get('phone_number'),
                        password = form.cleaned_data.get('password'),
                        display_name = form.cleaned_data.get('display_name'),
                        disabled = False
                    )
                    messages.success(request, f"User \'{new_user.uid}\' created successfully")
                    return JSONResponse({"status":True, "messages": messages_as_json(request)}, status=201)
                except Exception as e:
                    if (str(e) == 'Error while calling Auth service (INVALID_PHONE_NUMBER ). TOO_SHORT'):
                        messages.error(request, f"Phone number is invalid (Too Short). Phone number must be of 10-12 digits after country code!")
                        return JSONResponse({"status":False, "messages": messages_as_json(request)}, status=400) 
                    else:
                        messages.error(request, f"Error while registering user. Invalid input !")
                        return JSONResponse({"status":False, "messages": messages_as_json(request), "errors": str(e)}, status=400)
        else:
            form_errors_as_json(form)
            messages.error(request, f"Invalid input")
            return JSONResponse({"status":False, "messages": messages_as_json(request), "errors": form_errors_as_json(form)}, status=400)
    else:
        messages.error(request, f"Invalid request")
        return JSONResponse({"status":False, "messages": messages_as_json(request)}, status=405)

# @login_required
def user_update(request):
    if request.method == "POST":
        form = form_update(request.POST)
        if form.is_valid():
            try:
                user = auth.update_user(
                    form.cleaned_data.get('username'),
                    email = form.cleaned_data.get('email'),
                    phone_number = form.cleaned_data.get('phone_number')
                    # email_verified = True,
                    # password = form.cleaned_data.get('username'),
                    # display_name = form.cleaned_data.get('display_name'),
                    # photo_url = None,
                    # disabled = True
                )

                details = {
                    "first_name": form.cleaned_data.get('first_name'),
                    "last_name": form.cleaned_data.get('last_name'),
                    "blood_group_name": form.cleaned_data.get('blood_group_name'),
                    "country": form.cleaned_data.get('country'),
                    "state": form.cleaned_data.get('state'),
                    "city": form.cleaned_data.get('city'),
                    "area": form.cleaned_data.get('area')
                }
                user_put_detail(form.cleaned_data.get('username'), details)

                data = {
                    "user": user_record_to_json(user),
                    "user_details": details
                }

                messages.success(request, "Sucessfully updated user: {0}".format(user.uid))
                return JSONResponse({"status":True, "messages": messages_as_json(request), "data": data}, status=200) 
            except Exception as e:
                if(e.__class__.__name__ == 'PhoneNumberAlreadyExistsError'):
                    messages.error(request, f"A user with that phone number already exists. Try again with another number!")
                    return JSONResponse({"status":False, "messages": messages_as_json(request)}, status=400)
                else:
                    messages.error(request, f"Error while updating user")
                    return JSONResponse({"status":False, "messages": messages_as_json(request), "errors": str(e)}, status=400)
                    

        else:
            form_errors_as_json(form)
            messages.error(request, f"Invalid input")
            return JSONResponse({"status":False, "messages": messages_as_json(request), "errors": form_errors_as_json(form)}, status=400)
    else:
        messages.error(request, f"Invalid request")
        return JSONResponse({"status":False, "messages": messages_as_json(request)}, status=405)

def user_put_detail(username, details):
    try:
        doc_ref = db.collection("user_detail").document(username)
        doc_ref.set({
            "first_name": details['first_name'],
            "last_name": details['last_name'],
            "blood_group_name": details['blood_group_name'],
            "country": details['country'],
            "state": details['state'],
            "city": details['city'],
            "area": details['area']
        })
    except Exception as e:
        print(e)
        return False
    return True 
    
def user_get_detail(username):
    users_ref = db.collection("user_detail").document(username)
    doc = users_ref.get()
    if doc.exists:
        data = doc.to_dict()
        return data
    return {}

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

def item_add(request):
    if request.method == "POST":
        form = form_addItem(request.POST)
        if form.is_valid():
            unique_identifier = generate_unique_identifier()
            try:
                doc_ref = db.collection("items").document(form.cleaned_data.get('username')).collection('items').document(form.cleaned_data.get('name') + '_' + unique_identifier)
                doc_ref.set({
                    "id" : form.cleaned_data.get('name') + '_' + unique_identifier,
                    "name": form.cleaned_data.get('name'),
                    "price": form.cleaned_data.get('price'),
                    "quantity": form.cleaned_data.get('quantity'),
                    "expiry_date": form.cleaned_data.get('expiry_date'),
                    "purchase_date": form.cleaned_data.get('purchase_date'), #datetime.now().strftime('%Y-%m-%d'),
                    "description": form.cleaned_data.get('description'),
                })
                
                messages.error(request, "Successfully added item")
                return JSONResponse({"status":True, "messages": messages_as_json(request)}, status=201)   
            except Exception as e:
                messages.error(request, "Error while adding item")
                return JSONResponse({"status":False, "messages": messages_as_json(request), "errors": str(e)}, status=401)   
        else:
            form_errors_as_json(form)
            messages.error(request, f"Invalid input")
            return JSONResponse({"status":False, "messages": messages_as_json(request), "errors": form_errors_as_json(form)}, status=400)
    else:
        messages.error(request, f"Invalid request")
        return JSONResponse({"status":False, "messages": messages_as_json(request)}, status=405)

def item_get_all(request):
    users_ref = db.collection("items")
    docs = users_ref.stream()
    data = {}
    for doc in docs:
        data[doc.id] = doc.to_dict()
    messages.success(request, f"Successfully retrieved all items")
    return JSONResponse({"status":True, "data": data, "messages": messages_as_json(request)}, status=200)

def item_get(request):
    username = request.headers.get('username')
    users_ref = db.collection("items").document(username).collection('items')
    docs = users_ref.order_by("purchase_date", direction=firestore.Query.DESCENDING).stream()
    data = {}
    for doc in docs:
        data[doc.id] = doc.to_dict()
    messages.success(request, f"Successfully retrieved stock items data")
    return JSONResponse({"status":True, "data": data, "messages": messages_as_json(request)}, status=200)

def item_sell(request):
    if request.method == "POST":
        form = form_sellItem(request.POST)
        if form.is_valid():
            unique_identifier = generate_unique_identifier()
            try:
                if (form.cleaned_data.get('available_quantity') ==  form.cleaned_data.get('quantity')):
                    db.collection("items").document(form.cleaned_data.get('username')).collection('items').document(form.cleaned_data.get('id')).delete()
                else:
                    remaining_quantity = int(form.cleaned_data.get('available_quantity')) - int(form.cleaned_data.get('quantity'))
                    update_ref = db.collection("items").document(form.cleaned_data.get('username')).collection('items').document(form.cleaned_data.get('id'))
                    update_ref.update({"quantity": remaining_quantity})

                doc_ref = db.collection("sales").document(form.cleaned_data.get('username')).collection('sales').document(form.cleaned_data.get('name') + '_' + unique_identifier)
                doc_ref.set({
                    "id" : form.cleaned_data.get('name') + '_' + unique_identifier,
                    "name": form.cleaned_data.get('name'),
                    "price": form.cleaned_data.get('price'),
                    "quantity": form.cleaned_data.get('quantity'),
                    'sales_date': form.cleaned_data.get('sales_date'), #datetime.now().strftime('%Y-%m-%d'),
                    "expiry_date": form.cleaned_data.get('expiry_date'),
                    "purchase_date": form.cleaned_data.get('purchase_date'),
                    "description": form.cleaned_data.get('description'),
                })

                messages.error(request, "Successfully sold the item")
                return JSONResponse({"status":True, "messages": messages_as_json(request)}, status=200)   
            except Exception as e:
                messages.error(request, "Error while selling item")
                return JSONResponse({"status":False, "messages": messages_as_json(request), "errors": str(e)}, status=401)   
        else:
            form_errors_as_json(form)
            messages.error(request, f"Invalid input")
            return JSONResponse({"status":False, "messages": messages_as_json(request), "errors": form_errors_as_json(form)}, status=400)
    else:
        messages.error(request, f"Invalid request")
        return JSONResponse({"status":False, "messages": messages_as_json(request)}, status=405)

def item_get_sales(request):
    username = request.headers.get('username')
    users_ref = db.collection("sales").document(username).collection('sales')
    docs = users_ref.order_by("sales_date", direction=firestore.Query.DESCENDING).stream()
    data = {}
    for doc in docs:
        data[doc.id] = doc.to_dict()
    messages.success(request, f"Successfully retrieved sales items data")
    return JSONResponse({"status":True, "data": data, "messages": messages_as_json(request)}, status=200)

def item_get_expiry(request):
    username = request.headers.get('username')
    today = datetime.strptime(request.headers.get('today'), '%Y-%m-%d').date()
    users_ref = db.collection("items").document(username).collection('items')
    docs = users_ref.order_by("expiry_date", direction=firestore.Query.DESCENDING).stream()
    data = {}
    for doc in docs:
        data[doc.id] = doc.to_dict()
    data_expiry = {}
    for item in data:
        if(len(data[item]['expiry_date']) == 0):
            continue
        expiry_date = datetime.strptime(data[item]['expiry_date'], '%Y-%m-%d').date()
        days_difference = (expiry_date - today).days
        if(days_difference < 15):
            data_expiry[item] = data[item]
    messages.success(request, f"Successfully retrieved sales items data")
    return JSONResponse({"status":True, "data": data_expiry, "messages": messages_as_json(request)}, status=200)

def get_notifications(request):
    username = request.headers.get('username')
    today = datetime.strptime(request.headers.get('today'), '%Y-%m-%d').date()
    users_ref = db.collection("items").document(username).collection('items')
    docs = users_ref.order_by("expiry_date", direction=firestore.Query.DESCENDING).stream()
    data = {}
    for doc in docs:
        data[doc.id] = doc.to_dict()
    notifications = {}
    for item in data:
        if(len(data[item]['expiry_date']) == 0):
            continue
        expiry_date = datetime.strptime(data[item]['expiry_date'], '%Y-%m-%d').date()
        days_difference = (expiry_date - today).days
        
        if(days_difference < 15):
            notifications[item] = 'Your item \'' + str(data[item]['name']) + '\' is going to expire soon at ' + str(data[item]['expiry_date']) + f' ({days_difference} days remaining)'
        if(days_difference == 0):
            notifications[item] = 'Your item \'' + str(data[item]['name']) + '\' is expiring today which was bought on ' + str(data[item]['purchase_date'])
        if(days_difference < 0):
            notifications[item] = 'Your item \'' + str(data[item]['name']) + '\' has expired at ' + str(data[item]['expiry_date']) + '. It was purchased on ' + str(data[item]['purchase_date']) 
    
    messages.success(request, f"Successfully retrieved sales items data")
    return JSONResponse({"status":True, "data": notifications, "messages": messages_as_json(request)}, status=200)

def post_create(request):
    if request.method == "POST":
        form = form_post(request.POST)
        if form.is_valid():
            try:
                unique_identifier = generate_unique_identifier()
                if(form.cleaned_data.get('urgency_level') == 'emergency'):
                    doc_ref = db.collection("post_emergency").document(form.cleaned_data.get('username')+ '_' + unique_identifier)
                    doc_ref.set({
                        "username": form.cleaned_data.get('username'),
                        "create_ts": form.cleaned_data.get('create_ts'),
                        "urgency_level": form.cleaned_data.get('urgency_level'),
                        "blood_group": form.cleaned_data.get('blood_group'),
                        "country": form.cleaned_data.get('country'),
                        "state": form.cleaned_data.get('state'),
                        "city": form.cleaned_data.get('city'),
                        "area": form.cleaned_data.get('area'),
                        "title": form.cleaned_data.get('title'),
                        "content": form.cleaned_data.get('content'),
                        "total_reaction" : 0
                    })
                elif(form.cleaned_data.get('urgency_level') == 'post'):
                    doc_ref = db.collection("post_regular").document(form.cleaned_data.get('username')+ '_' + unique_identifier)
                    doc_ref.set({
                        "username": form.cleaned_data.get('username'),
                        "create_ts": form.cleaned_data.get('create_ts'),
                        "urgency_level": form.cleaned_data.get('urgency_level'),
                        "blood_group": form.cleaned_data.get('blood_group'),
                        "country": form.cleaned_data.get('country'),
                        "state": form.cleaned_data.get('state'),
                        "city": form.cleaned_data.get('city'),
                        "area": form.cleaned_data.get('area'),
                        "title": form.cleaned_data.get('title'),
                        "content": form.cleaned_data.get('content'),
                        "total_reaction" : 0
                    })
                else:
                    messages.error(request, f"Invalid input: Urgency Level not properly set!")
                    return JSONResponse({"status":False, "messages": messages_as_json(request), "errors": str(e)}, status=401)  

                messages.error(request, "Successfully created post")
                return JSONResponse({"status":True, "messages": messages_as_json(request)}, status=201)   
            except Exception as e:
                messages.error(request, "Error while creating post")
                return JSONResponse({"status":False, "messages": messages_as_json(request), "errors": str(e)}, status=401)   
        else:
            form_errors_as_json(form)
            messages.error(request, f"Invalid input")
            return JSONResponse({"status":False, "messages": messages_as_json(request), "errors": form_errors_as_json(form)}, status=400)
    else:
        messages.error(request, f"Invalid request")
        return JSONResponse({"status":False, "messages": messages_as_json(request)}, status=405)

def putreaction(request):
    if request.method == "POST":
        username = request.POST.get("username")
        post_id = request.POST.get("post_id")
        reaction = request.POST.get("reaction")
        level = request.POST.get("urgency_level")
        doc_ref = db.collection("reaction").document(username + '_%_' + post_id)
        doc_ref.set({
            "username": username,
            "post_id": post_id,
            "reaction": reaction,
        })
        value = -1 if(reaction == 0 or reaction == '0') else 1
        collection = 'post_emergency' if(level == 'emergency') else 'post_regular'
        post_ref = db.collection(collection).document(post_id)
        post_ref.update({"total_reaction": firestore.Increment(value)})

        messages.error(request, "Successfully updated reaction")
        return JSONResponse({"status": True, "messages": messages_as_json(request)}, status=201)
    else:
        messages.error(request, f"Invalid request")
        return JSONResponse({"status": False, "messages": messages_as_json(request)}, status=405)

def post_get_emergency(request):
    today = datetime.strptime(request.headers.get('today'), '%Y-%m-%d %H:%M:%S')
    username = request.headers.get('username')

    post_ref = db.collection("post_emergency")
    docs = post_ref.order_by("create_ts", direction=firestore.Query.DESCENDING).stream()

    reaction_ref = db.collection("reaction")
    reaction_doc = reaction_ref.where(filter=FieldFilter("username", "==", username)).stream()

    reactions = {}
    for reaction in reaction_doc:
        reactions[reaction.id] = reaction.to_dict()

    data = {}
    for doc in docs:
        data[doc.id] = doc.to_dict()
        data[doc.id]['create_ts'] = get_time_difference_in_words(today, datetime.strptime(data[doc.id]['create_ts'], '%Y-%m-%d %H:%M:%S')) + " ago"
        if(reactions.get(username + "_%_" + doc.id) != None):
            data[doc.id]['user_reaction'] = reactions[username + "_%_" + doc.id]['reaction']
        else:
            data[doc.id]['user_reaction'] = 0
   
    messages.success(request, f"Successfully retrieved all emergency posts")
    return JSONResponse({"status":True, "data": data, "messages": messages_as_json(request)}, status=200)

def post_get_regular(request):
    today = datetime.strptime(request.headers.get('today'), '%Y-%m-%d %H:%M:%S')
    username = request.headers.get('username')

    post_ref = db.collection("post_regular")
    docs = post_ref.order_by("create_ts", direction=firestore.Query.DESCENDING).stream()

    reaction_ref = db.collection("reaction")
    reaction_doc = reaction_ref.where(filter=FieldFilter("username", "==", username)).stream()

    reactions = {}
    for reaction in reaction_doc:
        reactions[reaction.id] = reaction.to_dict()

    data = {}
    for doc in docs:
        data[doc.id] = doc.to_dict()
        data[doc.id]['create_ts'] = get_time_difference_in_words(today, datetime.strptime(data[doc.id]['create_ts'], '%Y-%m-%d %H:%M:%S')) + " ago"
        if(reactions.get(username + "_%_" + doc.id) != None):
            data[doc.id]['user_reaction'] = reactions[username + "_%_" + doc.id]['reaction']
        else:
            data[doc.id]['user_reaction'] = 0
   
    messages.success(request, f"Successfully retrieved all emergency posts")
    return JSONResponse({"status":True, "data": data, "messages": messages_as_json(request)}, status=200)

def get_alerts(request):
    username = request.headers.get('username')
    user_details = user_get_detail(username)
    today = datetime.strptime(request.headers.get('today'), '%Y-%m-%d %H:%M:%S')
    post_ref = db.collection("post_emergency")
    docs = post_ref.order_by("create_ts", direction=firestore.Query.DESCENDING).stream()
    data = {}
    for doc in docs:
        data[doc.id] = doc.to_dict()
    alerts = {}

    for item in data:
        if (user_details['country'] == data[item]['country']) and (user_details['state'] == data[item]['state']):
            create_ts = datetime.strptime(data[item]['create_ts'], '%Y-%m-%d %H:%M:%S')
            time_difference = get_time_difference_in_words(today, create_ts)
            alerts[item] = 'User ' + str(data[item]['username']) + ' has requested blood type ' + str(data[item]['blood_group']) + ' in your area about ' + str(time_difference) + ' ago'

    messages.success(request, f"Successfully retrieved all emergency posts")
    return JSONResponse({"status":True, "data": alerts, "messages": messages_as_json(request)}, status=200)



