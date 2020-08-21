import speech_recognition as sr

for index, name in enumerate(sr.Microphone.list_microphone_names()):
    print(
        'Microphone with name "{1}" found for `Microphone(device_index={0})`'.format(
            index, name
        )
    )

r = sr.Recognizer()
with sr.Microphone() as source:
    print("Listening:")
    while True:
        audio = r.listen(source, 1, 5)
        try:
            text = r.recognize_google(audio, language="pt-BR")
            print("You said : {}".format(text))
        except Exception as e:
            print("Sorry could not recognize what you said")
