import socket
import speech_recognition as sr

def recognize_speech_from_mic(recognizer, microphone):
    if not isinstance(recognizer, sr.Recognizer):
        raise TypeError("`recognizer` must be `Recognizer` instance")
    if not isinstance(microphone, sr.Microphone):
        raise TypeError("`microphone` must be `Microphone` instance")
    with microphone as source:
        recognizer.adjust_for_ambient_noise(source)
        print('Recording...')
        audio = recognizer.listen(source)

    response = {
        "success": True,
        "error": None,
        "transcription": None
    }
    try:
        response["transcription"] = recognizer.recognize_google(audio, language='tr-tr')
    except sr.RequestError:
        response["success"] = False
        response["error"] = "API unavailable"
    except sr.UnknownValueError:
        response["error"] = "Unable to recognize speech"
    return response

def Main():
    host = '172.16.58.16'
    port = 12345
    s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    s.connect((host,port))
    
    micro = sr.Microphone()
    recko = sr.Recognizer()	
    while True:
        trkrp_mes = recognize_speech_from_mic(recko, micro)
        s.send(trkrp_mes["transcription"].encode('utf-8'))
        data = s.recv(1024)
        print('Received from the server :',str(data.decode('utf-8')))
        cont_ans = input('\nDo you want to continue(y/n) :')
        if cont_ans == 'y':
            continue
        else:
            break
        
    s.close()

if __name__ == '__main__':
	Main()
