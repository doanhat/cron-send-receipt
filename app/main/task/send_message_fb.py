import json
import os

from dotenv import load_dotenv
from google.cloud import secretmanager

from app.main.config.environment.environment_configuration import PROJECT_ID, SES_SECRET_ID, LOG_SECRET_ID, \
    THREAD_ID
from app.main.helper.gcp_helper import get_secret, add_secret
from app.main.helper.logger import logger
from app.main.resource.fbchat import Client
from app.main.resource.fbchat.models import *

load_dotenv("env/.env")
CLIENT = secretmanager.SecretManagerServiceClient()


def get_client():
    try:
        # Load the session cookies
        cookies = json.loads(get_secret(CLIENT, PROJECT_ID, SES_SECRET_ID))
        client = Client('email', 'password', session_cookies=cookies)
    except Exception as e:
        logger.error(e)
        # If it fails, never mind, we'll just login again
        fb_login = json.loads(get_secret(CLIENT, PROJECT_ID, LOG_SECRET_ID))
        user = fb_login.get("FB_USER_EMAIL_ADDRESS")
        password = fb_login.get("FB_USER_PASSWORD")
        client = Client(user, password)
        cookies = client.getSession()
        add_secret(CLIENT, PROJECT_ID, SES_SECRET_ID, json.dumps(cookies))

    return client


def send_msg_to_thread(message):
    client = get_client()
    logger.info("Login succeed")
    try:
        logger.info(THREAD_ID)
        client.send(Message(text=message), thread_id=THREAD_ID, thread_type=ThreadType.GROUP)
    except FBchatFacebookError as e:
        logger.error(e)
        try:
            client.send(Message(text=message), thread_id=THREAD_ID, thread_type=ThreadType.USER)
        except Exception as e:
            raise e

    add_secret(CLIENT, PROJECT_ID, SES_SECRET_ID, json.dumps(client.getSession()))
    client.logout()
