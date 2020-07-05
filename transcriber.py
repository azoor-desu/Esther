import wave
import requests

def TranscribeAudiofile(this,audiofile):
    #Can be a universal method for multiple different systems (e.g. Julius, wit.ai etc)
    #For now, customize for wit.ai.
    #wit.ai also returns the intents and everything already, so we'll have to account for that.

    # Flow: Snowboy becomes active for keyword,
    # Keyword detected, snowboy stops, 12 sec/threshold recording starts
    # Clip recorded, send it to transcriber.py.
    # transcriber software returns a string.
    
    headers = {'Authorization': 'Bearer P227AKWSRRL3THQXYRPQYNXMETRW3XLH',
                         'accept': 'application/json',
                         'Content-Type': 'audio/wav'}

    data = audiofile.read()
    r = requests.post('https://api.wit.ai/speech?v=20200705', data=data, headers=headers)

    try:
        r.raise_for_status()
        text = r.json()
    except requests.exceptions.HTTPError:
        print("HTTP ERROR")
    except requests.exceptions.RequestException:
        print("REQ FAILED ERROR")
    except KeyError:
        print("KEY ERROR")
    else:
        transcribed = []
        #if text:
            #transcribed.append(text.upper())
        print(text)