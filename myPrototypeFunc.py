import json
import os
import logging
#from pprint import pprint

# Defining Event Handler
def lambda_handler(event, context):
    if (event["session"]["application"]["applicationId"] !=
            "amzn1.ask.skill.0ec82a30-cdd0-4e05-961a-27cafed3eda1"):
        raise ValueError("Invalid Application ID")
    
    if event["session"]["new"]:
        on_session_started({"requestId": event["request"]["requestId"]}, event["session"])

    if event["request"]["type"] == "LaunchRequest":
        return on_launch(event["request"], event["session"])
    elif event["request"]["type"] == "IntentRequest":
        return on_intent(event["request"], event["session"])
    elif event["request"]["type"] == "SessionEndedRequest":
        return on_session_ended(event["request"], event["session"])

def on_session_started(session_started_request, session):
    print("Starting new session.")

# Start Session
def on_launch(launch_request, session):
    return get_welcome_response()

# Terminate Session
def on_session_ended(session_ended_request, session):
    print("Ending session.")
    # Cleanup goes here...

# Welcome Response
def get_welcome_response():
    session_attributes = {}
    card_title = "Orvito"
    speech_output = "Welcome to Orvito SmartHome. " 
    reprompt_text = "Please make a request, " \
                    "for example Turn lights on in the bedroom."
    should_end_session = False
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))


# Stop/Cancel Orvito Intent
def handle_session_end_request():
    card_title = "Orvito - Thanks"
    speech_output = "Thank you for using Orvito!"
    should_end_session = True
    return build_response({}, build_speechlet_response(card_title, speech_output, None, should_end_session))


# Intent Calls
def on_intent(intent_request, session):
    intent = intent_request["intent"]
    intent_name = intent_request["intent"]["name"]

    if intent_name == "AskOrvito":
        return ask_orvito(intent)
    elif intent_name == "AMAZON.HelpIntent":
        return get_welcome_response()
    elif intent_name == "AMAZON.CancelIntent" or intent_name == "AMAZON.StopIntent":
        return handle_session_end_request()
    else:
        raise ValueError("Invalid intent")


def ask_orvito(intent):
    session_attributes = {}
    card_title = "Ask Orvito"
    speech_output = "I didn't quite understand what you requested for. " \
                    "Please try again."
    reprompt_text = "I'm sorry I didn't understand what you requested for. " \
                    "Try saying Turn on the Lights in the master bedroom "
    should_end_session = False


    CMDVALUE = intent["slots"]["cmdvalue"]["value"]
    CMDVALUENUM = ""  
    if CMDVALUE.lower()=="on":
        CMDVALUENUM="1"
    else:
        CMDVALUENUM="0"
    
    GRPNAME = intent["slots"]["groupname"]["value"]
    NODENAME = intent["slots"]["nodename"]["value"]

    
    #EmbeddedDriverScript
    sessionId = '<insert session Id here>'
    sessionCurlCall = 'curl --data "sessionId=' + sessionId + '&" https://iot.orvito.com/api/v1.0/getalldata'

    output = os.popen(sessionCurlCall)

    data = json.loads(output.read())

    listOfKeys = data.keys()

    nodeDataKeys = data['getallnodes'].keys()
    nodeData = data['getallnodes']['nodeList']


    grpIds = []
    grpNames = []
    grpNodes = []
    favourite = []

    for i in range(len(nodeData)):
        grpIds.append(nodeData[i]['grpId'])
        grpNames.append(nodeData[i]['grpName'])
        grpNodes.append(nodeData[i]['groupNodes'])
        favourite.append(nodeData[i]['favourite'])

    numNodesInGrp = [len(i) for i in grpNodes]
    nodeIds = []
    nodeNames = []
    grpNos = 0

    for grp in grpNodes:
        nodeIds.append([])
        nodeNames.append([])
        for node in grp:
            nodeIds[grpNos].append(node['nodeId'])
            nodeNames[grpNos].append(node['nodeName'])
        grpNos+=1

    # Group Node Control
    cmdId = str(1) #this static cmdId states the type of command performed, such as 1-ON/OFF, 2-Dimmer something like that
    getGroupNo = 0
    getNodeNo = 0

    #Unknown GroupName
    for i in range(grpNos):
        if grpNames[i].lower()==GRPNAME.lower():
            getGroupNo = i
            break
        else:
            if(i==(grpNos-1)):
                card_title = "Ask Orvito GroupError" 
                speech_output = "I'm sorry, the requested " + GRPNAME + " doesn't exist."
                reprompt_text = ""
                return build_response(session_attributes, build_speechlet_response(card_title, speech_output, reprompt_text, should_end_session))
                
                
    numNodeIds = numNodesInGrp[getGroupNo]
    staticNumNodeIds = 1

    #Unknown Nodename
    for i in range(numNodeIds):
        if nodeNames[getGroupNo][i].lower()==NODENAME.lower():
            getNodeNo = i
            break
        else:
            if(i==(numNodeIds-1)):
                card_title = "Ask Orvito NodeError" 
                speech_output = "I'm sorry, the requested " + NODENAME + " doesn't exist."
                reprompt_text = ""
                return build_response(session_attributes, build_speechlet_response(card_title, speech_output, reprompt_text, should_end_session))
                


    nodeId = nodeIds[getGroupNo][getNodeNo]

    grpNodeControlCurlCall = 'curl --data "cmdId=' + cmdId + '&cmdVal=' + CMDVALUENUM + '&numNodeIds=' + str(staticNumNodeIds) + '&nodeId-0=' + str(nodeId) + '&sessionId=' + sessionId + '&" https://iot.orvito.com/api/v1.0/grpnodecontrol'
    #print(grpNodeControlCurlCall)
    os.popen(grpNodeControlCurlCall)
    card_title = "Ask Orvito" + GRPNAME.title()
    speech_output = "Turning " + CMDVALUE + " the " + NODENAME + " in " + GRPNAME
    reprompt_text = ""

    return build_response(session_attributes, build_speechlet_response(card_title, speech_output, reprompt_text, should_end_session))




# Speech Output
def build_speechlet_response(title, output, reprompt_text, should_end_session):
    return {
        "outputSpeech": {
            "type": "PlainText",
            "text": output
        },
        "card": {
            "type": "Simple",
            "title": title,
            "content": output
        },
        "reprompt": {
            "outputSpeech": {
                "type": "PlainText",
                "text": reprompt_text
            }
        },
        "shouldEndSession": should_end_session
    }

def build_response(session_attributes, speechlet_response):
    return {
        "version": "1.0",
        "sessionAttributes": session_attributes,
        "response": speechlet_response
    }
