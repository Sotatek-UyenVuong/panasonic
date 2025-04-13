# AI-NoteX/commons/email_sender_campaigns.py

import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()
token = os.getenv("SENDER_API_KEY")

headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json",
    "Accept": "application/json",
}

def create_subscriber(email, firstname, lastname, groups, fields=None, phone=None, trigger_automation=True):
    url = "https://api.sender.net/v2/subscribers"
    payload = {
        "email": email,
        "firstname": firstname,
        "lastname": lastname,
        "groups": groups,
        "fields": fields,
        "phone": phone,
        "trigger_automation": trigger_automation
    }
    response = requests.post(url, headers=headers, json=payload)
    return response.json()

def update_subscriber(identifier, firstname=None, lastname=None, groups=None, fields=None, 
                      subscriber_status=None, phone=None, trigger_automation=True, 
                      transactional_email_status=None, sms_status=None):
    url = f"https://api.sender.net/v2/subscribers/{identifier}"
    payload = {
        "firstname": firstname,
        "lastname": lastname,
        "groups": groups,
        "fields": fields,
        "subscriber_status": subscriber_status,
        "phone": phone,
        "trigger_automation": trigger_automation,
        "transactional_email_status": transactional_email_status,
        "sms_status": sms_status
    }
    response = requests.patch(url, headers=headers, json=payload)
    return response.json()

def delete_subscribers(subscribers):
    url = "https://api.sender.net/v2/subscribers"
    payload = {
        "subscribers": subscribers
    }
    response = requests.delete(url, headers=headers, json=payload)
    return response.json()

def add_subscriber_to_group(group_id, subscribers, trigger_automation=True):
    url = f"https://api.sender.net/v2/subscribers/groups/{group_id}"
    payload = {
        "subscribers": subscribers,
        "trigger_automation": trigger_automation
    }
    response = requests.post(url, headers=headers, json=payload)
    return response.json()

def remove_subscriber_from_group(group_id, subscribers):
    url = f"https://api.sender.net/v2/subscribers/groups/{group_id}"
    payload = {
        "subscribers": subscribers
    }
    response = requests.delete(url, headers=headers, json=payload)
    return response.json()

# Ví dụ sử dụng các hàm
# create_subscriber("support@sender.net", "Sender", "Support", ["eZVD4w", "b2vAR1"])
# print(update_subscriber("hung.dang@sotatek.com", firstname="NewSender", subscriber_status="ACTIVE", sms_status="UNSUBSCRIBED", transactional_email_status="BOUNCED"))
print(delete_subscribers(["hung.dang@sotatek.com"]))
# add_subscriber_to_group("dBQ5Yn", ["hung.dang@sotatek.com"])
# remove_subscriber_from_group("eZVD4w", ["support@sender.net", "support+2@sender.net"])