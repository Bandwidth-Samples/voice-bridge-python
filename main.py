import http
import os
import sys

import bandwidth
from bandwidth.models.bxml import Response as BxmlResponse
from bandwidth.models.bxml import SpeakSentence, Ring, Bridge
from fastapi import FastAPI, Response
import uvicorn

try:
    BW_USERNAME = os.environ['BW_USERNAME']
    BW_PASSWORD = os.environ['BW_PASSWORD']
    BW_ACCOUNT_ID = os.environ['BW_ACCOUNT_ID']
    BW_VOICE_APPLICATION_ID = os.environ['BW_VOICE_APPLICATION_ID']
    BW_NUMBER = os.environ['BW_NUMBER']
    USER_NUMBER = os.environ['USER_NUMBER']
    LOCAL_PORT = int(os.environ['LOCAL_PORT'])
    BASE_CALLBACK_URL = os.environ['BASE_CALLBACK_URL']
except KeyError as e:
    print(f"Please set the environmental variables defined in the README\n\n{e}")
    sys.exit(1)
except ValueError as e:
    print(f"Please set the LOCAL_PORT environmental variable to an integer\n\n{e}")
    sys.exit(1)

app = FastAPI()

bandwidth_configuration = bandwidth.Configuration(
    username=BW_USERNAME,
    password=BW_PASSWORD
)

bandwidth_api_client = bandwidth.ApiClient(bandwidth_configuration)
bandwidth_calls_api_instance = bandwidth.CallsApi(bandwidth_api_client)


@app.post('/callbacks/inboundCall', status_code=http.HTTPStatus.OK)
def inbound_call(inbound_callback: bandwidth.models.AnswerCallback):
    call_body = bandwidth.models.CreateCall(
        to=USER_NUMBER,
        from_=BW_NUMBER,
        answer_url=f"{BASE_CALLBACK_URL}/callbacks/outboundCall",
        application_id=BW_VOICE_APPLICATION_ID,
        tag=inbound_callback.call_id
    )

    try:
        bandwidth_calls_api_instance.create_call(BW_ACCOUNT_ID, call_body=call_body)
    except bandwidth.ApiException as e:
        print(f"Error creating call: {e}")

    speak_sentence = SpeakSentence(text="Hold while we connect you.")
    ring = Ring(duration=30)
    bxml_response = BxmlResponse([speak_sentence, ring])

    return Response(content=bxml_response.to_bxml(), media_type="application/xml")


@app.post('/callbacks/outboundCall', status_code=http.HTTPStatus.OK)
def outbound_call(inbound_callback: bandwidth.models.AnswerCallback):
    speak_sentence = SpeakSentence(text="Hold while we connect you. We will begin to bridge you now.")
    bridge = Bridge(target_call=inbound_callback.tag)
    bxml_response = BxmlResponse([speak_sentence, bridge])

    return Response(content=bxml_response.to_bxml(), media_type="application/xml")


if __name__ == '__main__':
    uvicorn.run("main:app", port=LOCAL_PORT, reload=True)
