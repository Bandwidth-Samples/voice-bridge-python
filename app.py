from bandwidth.bandwidth_client import BandwidthClient
from bandwidth.voice.models.api_create_call_request import ApiCreateCallRequest
from bandwidth.voice.bxml.response import Response
from bandwidth.voice.bxml.verbs import *

from flask import Flask, request

import os
import sys
import json

try:
    BANDWIDTH_USERNAME = os.environ['BANDWIDTH_USERNAME']
    BANDWIDTH_PASSWORD = os.environ['BANDWIDTH_PASSWORD']
    BANDWIDTH_ACCOUNT_ID = os.environ['BANDWIDTH_ACCOUNT_ID']
    BANDWIDTH_VOICE_APPLICATION_ID = os.environ['BANDWIDTH_VOICE_APPLICATION_ID']
    BANDWIDTH_PHONE_NUMBER = os.environ['BANDWIDTH_PHONE_NUMBER']
    MASKED_PHONE_NUMBER = os.environ['MASKED_PHONE_NUMBER']
    PORT = os.environ['PORT']
    BASE_URL = os.environ['BASE_URL']
except:
    print("Please set the environmental variables defined in the README")
    sys.exit(1)

bandwidth_client = BandwidthClient(
    voice_basic_auth_user_name=BANDWIDTH_USERNAME,
    voice_basic_auth_password=BANDWIDTH_PASSWORD
)

voice_client = bandwidth_client.voice_client.client

app = Flask(__name__)

@app.route('/callbacks/inboundCall', methods=['POST'])
def inbound_call():
    callback_data = json.loads(request.data)

    body = ApiCreateCallRequest()
    body.mfrom = BANDWIDTH_PHONE_NUMBER
    body.to = MASKED_PHONE_NUMBER 
    body.answer_url = BASE_URL + '/callbacks/outboundCall' 
    body.application_id = BANDWIDTH_VOICE_APPLICATION_ID
    body.tag = callback_data['callId']

    voice_client.create_call(BANDWIDTH_ACCOUNT_ID, body=body)

    response = Response()
    speak_sentence = SpeakSentence(
        sentence="Hold while we connect you."
    )
    ring = Ring(
        duration=30
    )

    response.add_verb(speak_sentence)
    response.add_verb(ring)
    return response.to_bxml()

@app.route('/callbacks/outboundCall', methods=['POST'])
def outbound_call():
    callback_data = json.loads(request.data)

    response = Response()
    speak_sentence = SpeakSentence(
        sentence="Hold while we connect you. We will begin to bridge you now."
    )
    bridge = Bridge(
        call_id=callback_data['tag']
    )

    response.add_verb(speak_sentence)
    response.add_verb(bridge)
    return response.to_bxml()

if __name__ == '__main__':
    app.run(port=PORT)
