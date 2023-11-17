import os
import json
from django.contrib import messages
from collections import defaultdict
import random
import string
from datetime import datetime


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def messages_as_json(request):
    message_dict = defaultdict(list)
    for message in messages.get_messages(request):
        message_dict[message.tags] = message.message
        message_dict['attributes'].append(message.__dict__)
    return message_dict

def form_errors_as_json(form):
    # print(dict(form.errors))
    # print(form.errors.as_data())
    # print(form.errors.as_json())
    # print(json.loads(form.errors.as_json()))
    return json.loads(form.errors.as_json())

def location_info_Nepal():
    print(BASE_DIR)
    # os.path.join(BASE_DIR, 'assets/firebase_config.json')
    return json.load(open(os.path.join(BASE_DIR, 'assets/location_info_Nepal.json')))


def user_record_to_json(user_record):
    # Convert the Firebase UserRecord to a Python dictionary
    user_data = {
        'uid': user_record.uid,
        'email': user_record.email,
        'email_verified': user_record.email_verified,
        'display_name': user_record.display_name,
        'photo_url': user_record.photo_url,
        'phone_number': user_record.phone_number,
        'disabled': user_record.disabled,
        'metadata': {
            'creation_time': user_record.user_metadata.creation_timestamp,
            'last_sign_in_time': user_record.user_metadata.last_sign_in_timestamp,
            'last_active': user_record.user_metadata.last_refresh_timestamp,
        },
        'custom_claims': user_record.custom_claims,
    }
    return user_data

def generate_unique_identifier(length = 8):
    characters = string.ascii_letters + string.digits
    current_time_seed = int(datetime.now().timestamp())
    random.seed(current_time_seed)
    identifier = ''.join(random.choice(characters) for _ in range(length))
    return identifier