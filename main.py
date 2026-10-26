import http
import os
import sys

import bandwidth
from bandwidth.models.bxml import Response as BxmlResponse
from bandwidth.models.bxml import SpeakSentence, Ring, Bridge, Hangup
from fastapi import FastAPI, Response
from fastapi.exceptions import RequestValidationError
import uvicorn

try:
    BW_ACCOUNT_ID = os.environ['BW_ACCOUNT_ID']
    BW_CLIENT_ID = os.environ['BW_CLIENT_ID']
    BW_CLIENT_SECRET = os.environ['BW_CLIENT_SECRET']
    BW_VOICE_APPLICATION_ID = os.environ['BW_VOICE_APPLICATION_ID']
    BW_NUMBER = os.environ['BW_NUMBER']
    USER_NUMBER = os.environ['USER_NUMBER']
    BASE_CALLBACK_URL = os.environ['BASE_CALLBACK_URL']
    LOCAL_PORT = int(os.environ['LOCAL_PORT'])
except KeyError as e:
    print(f"Please set the environmental variables defined in the README\n\n{e}")
    sys.exit(1)
except ValueError as e:
    print(f"Please set the LOCAL_PORT environmental variable to an integer\n\n{e}")
    sys.exit(1)

app = FastAPI()

bandwidth_configuration = bandwidth.Configuration(
    client_id=BW_CLIENT_ID,
    client_secret=BW_CLIENT_SECRET
)

bandwidth_api_client = bandwidth.ApiClient(bandwidth_configuration)
bandwidth_calls_api_instance = bandwidth.CallsApi(bandwidth_api_client)


@app.exception_handler(RequestValidationError)
def invalid_request(request, exc):
    return Response(status_code=http.HTTPStatus.BAD_REQUEST)


@app.post("/callbacks/inbound/voice", status_code=http.HTTPStatus.OK)
def inbound_voice(initiate_callback: bandwidth.models.InitiateCallback):
    if initiate_callback.event_type != "initiate":
        print(f"Unexpected event type {initiate_callback.event_type} received")
        return Response(status_code=http.HTTPStatus.BAD_REQUEST)

    create_call_body = bandwidth.CreateCall(
        application_id=BW_VOICE_APPLICATION_ID,
        to=USER_NUMBER,
        var_from=BW_NUMBER,
        answer_url=f"{BASE_CALLBACK_URL}/callbacks/outbound/voice",
        tag=initiate_callback.call_id
    )

    try:
        bandwidth_calls_api_instance.create_call(BW_ACCOUNT_ID, create_call_body)
        bxml = BxmlResponse([SpeakSentence(text="Hold while we connect you."), Ring(duration=30)])
    except Exception as e:
        print(f"Failed to create call: {e}")
        bxml = BxmlResponse([SpeakSentence(text="An error occurred. Ending call."), Hangup()])

    return Response(content=bxml.to_bxml(), media_type="application/xml")


@app.post("/callbacks/outbound/voice", status_code=http.HTTPStatus.OK)
def outbound_voice(answer_callback: bandwidth.models.AnswerCallback):
    bxml = BxmlResponse()

    match answer_callback.event_type:
        case "answer":
            speak_sentence = SpeakSentence(text="Hold while we connect you. We will begin to bridge you now.")
            bridge = Bridge(target_call=answer_callback.tag)
            bxml.add_verb(speak_sentence)
            bxml.add_verb(bridge)
        case "disconnect":
            print(f"Call {answer_callback.call_id} has disconnected")
        case _:
            print(f"Unexpected event type {answer_callback.event_type} received")

    return Response(content=bxml.to_bxml(), media_type="application/xml")


if __name__ == "__main__":
    uvicorn.run("main:app", port=LOCAL_PORT, reload=True)
