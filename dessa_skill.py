import requests
import json



#####################################
#### RESPONSE BUILDER FUNCTIONS. ####
#####################################
def build_speechlet_response(title, output, reprompt_text, should_end_session) :
    """
    Build a speechlet JSON representation of the title, output text, 
    reprompt text & end of session
    """

    return {
        "outputSpeech" : {
            "type" : "PlainText",
            "text" : output
        },
        "card" : {
            'type': 'Simple',
            'title': title,
            'content': output
        },
        'reprompt': {
            'outputSpeech': {
                'type': 'PlainText',
                'text': reprompt_text
            }
        },
        'shouldEndSession': should_end_session
    }

def build_response(session_attributes, speechlet_response) :
    """
    Build the full response JSON from the speechlet response
    """

    return {
        'version': '1.0',
        'sessionAttributes': session_attributes,
        'response': speechlet_response
    }



###################################
#### SKILL BEHAVIOUR FUNCTIONS ####
###################################
def get_daily_fractals() :

    # Get daily fractal achievements from gw2 api.
    r = requests.get("https://api.guildwars2.com/v2/achievements/daily")
    dailies = r.json()["fractals"]

    # Separate achievements into lists of daily fractals and recommended scales.
    daily_fractals = []
    daily_recommended = []
    for achievement in dailies :
        achievement_id = achievement["id"]
        achievement_name = requests.get("https://api.guildwars2.com/v2/achievements/{}".format(achievement_id)).json()["name"]

        # Process Recommended Fractal Scale.
        if (achievement_name.startswith("Daily Recommended")) :
            parts = achievement_name.split()
            daily_recommended.append(parts[-1])
        
        # Process Daily Fractal.
        else :
            achievement_name = achievement_name.replace("Daily Tier ", "")
            achievement_name = "".join([c for c in achievement_name if not c.isdigit()])
            achievement_name = achievement_name.strip()
            daily_fractals.append(achievement_name)

    # Remove duplicates from dailies list.
    daily_fractals = list(set(daily_fractals))

    # Create list of daily fractals as a string.
    dailies_string = ""
    for fractal in daily_fractals :
        if (not fractal == daily_fractals[-1]) :
            dailies_string = dailies_string + fractal + ", "
        else :
            dailies_string = dailies_string[:-2]+ " and " + fractal

    # Create list of recommended fractals as a string.
    recs_string = ""
    for scale in daily_recommended :
        if (not scale == daily_recommended[-1]) :
            recs_string = recs_string + scale + " {}, ".format(get_fractal_at_scale(int(scale), verbose = False))
        else :
            recs_string = recs_string[:-2] + " and " + scale + " {}".format(get_fractal_at_scale(int(scale), verbose = False))

    # Assemble Response.
    response = "Today's daily fractals are {}. Today's recommended fractal scales are {}.".format(dailies_string, recs_string)
    return response

def get_fractal_at_scale(scale, verbose = True) :

    # Convert scale to integer.
    try :
        scale = int(scale)
    except ValueError :
        if (verbose == True) :
            return "No fractal is known to exist at scale {}.".format(scale)
        else :
            return "Unknown"

    # Reject scale if out of bounds (0, 100), or if not integer.
    if (not isinstance(scale, int) or scale < 0 or scale > 100) :
        if (verbose == True) :
            return "No fractal is known to exist at scale {}.".format(scale)
        else :
            return "Unknown"

    with open("fractal_data.json", "r") as scales_file :
        scales = json.load(scales_file)

        for fractal_name, fractal_scales in scales.items() :
            if scale in fractal_scales :
                if (verbose == True) :
                    return "The fractal at scale {} is {}".format(scale, fractal_name)
                else :
                    return fractal_name

def get_welcome_response() :
    session_attributes = {}
    card_title = "Hello"
    speech_output = "Welcome to the Mistlock Observatory. Ask me what today's daily fractals are, or about which fractal exists at different difficulty scales."
    reprompt_text = "I'm not sure I understand. Try asking me for today's daily fractals, or which fratcal exists at a specific difficulty scale."
    should_end_session = False
    return build_response(session_attributes, build_speechlet_response(card_title, speech_output, reprompt_text, should_end_session))

def get_session_end_response() :
    session_attributes = {}
    card_title = "Session Ended"
    speech_output = "Good luck in exploring the fractals, please tread carefully!"
    should_end_session = True
    return build_response(session_attributes, build_speechlet_response(card_title, speech_output, None, should_end_session))

def get_daily_fractals_response() :
    session_attributes = {}
    card_title = "Today's Daily Fractals"
    speech_output = get_daily_fractals()
    should_end_session = True
    return build_response(session_attributes, build_speechlet_response(card_title, speech_output, None, should_end_session))

def get_fractal_at_scale_response(scale) :
    session_attributes = {}
    card_title = "Fractal at Difficulty Scale {}".format(scale)
    speech_output = get_fractal_at_scale(scale)
    should_end_session = True
    return build_response(session_attributes, build_speechlet_response(card_title, speech_output, None, should_end_session))



###############################
#### Intent Event Handlers ####
###############################
def on_session_started(session_started_request, session):
    """ Called when the session starts """
    print("on_session_started requestId=" + session_started_request['requestId'] + ", sessionId=" + session['sessionId'])

def on_launch(launch_request, session):
    """ Called when the user launches the skill without specifying what they want """
    print("on_launch requestId=" + launch_request['requestId'] +
          ", sessionId=" + session['sessionId'])
    # Dispatch to your skill's launch
    return get_welcome_response()

def on_session_ended(session_ended_request, session):
    """ Called when the user ends the session. Is not called when the skill returns should_end_session=true """
    print("on_session_ended requestId=" + session_ended_request['requestId'] + ", sessionId=" + session['sessionId'])

def on_intent(intent_request, session):
    """ Called when the user specifies an intent for this skill """
    print("on_intent requestId=" + intent_request['requestId'] +
          ", sessionId=" + session['sessionId'])

    intent = intent_request['intent']
    intent_name = intent_request['intent']['name']

    # Dispatch to your skill's intent handlers
    if intent_name == "GetDailyFractals" :
        return get_daily_fractals_response()
    if intent_name == "GetFractalAtScale" :
        scale = intent["slots"]["fractalScale"]["value"]
        return get_fractal_at_scale_response(scale)
    elif intent_name == "AMAZON.HelpIntent" :
        return get_welcome_response()
    elif intent_name == "AMAZON.CancelIntent" or intent_name == "AMAZON.StopIntent" :
        return get_session_end_response()
    else:
        raise ValueError("Invalid intent")



###################################
#### Main Lambda Event Handler ####
###################################
def lambda_handler(event, context):
    """ Route the incoming request based on type (LaunchRequest, IntentRequest,
    etc.) The JSON body of the request is provided in the event parameter.
    """
    print("event.session.application.applicationId=" + event['session']['application']['applicationId'])
    if event['session']['new']:
        on_session_started({'requestId': event['request']['requestId']},
                           event['session'])
    if event['request']['type'] == "LaunchRequest":
        return on_launch(event['request'], event['session'])
    elif event['request']['type'] == "IntentRequest":
        return on_intent(event['request'], event['session'])
    elif event['request']['type'] == "SessionEndedRequest":
        return on_session_ended(event['request'], event['session'])
