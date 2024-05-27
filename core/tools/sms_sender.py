import json, requests, hashlib
import os
from dotenv import load_dotenv


load_dotenv()

# config
rocketsms_login = os.environ.get('ROCKETSMS_LOGIN')
rocketsms_password = os.environ.get('ROCKETSMS_PASSWORD')
rocketsms_passhash = hashlib.md5(rocketsms_password.encode('utf-8')).hexdigest()
rocketsms_url = os.environ.get('ROCKETSMS_URL')


def sendsms(phone, message):
    data = {'username': rocketsms_login, 'password': rocketsms_passhash, 'phone': phone, 'text': message,
            'priority': 'true'}
    try:
        # request = requests.post(rocketsms_url, data=data)
        # result = request.json()
        # status = result['status']
        print("Успешно отправлено")
        print(message)
    except Exception as e:
        print('Cannot send SMS: bad or no response from RocketSMS.')
        print(e)
    else:
        print("Не отправлено")
        # if (status == 'SENT') | (status == 'QUEUED'):
        #     print('SMS accepted, status: {}'.format(status))
        # else:
        #     print('SMS rejected, status: {}'.format(status))
