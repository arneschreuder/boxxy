import io
import os
import re
import subprocess
import sys

import numpy as np
import openai
import sounddevice as sd
import speech_recognition as sr
from dotenv import load_dotenv
from pynput import keyboard
from pynput.keyboard import Key, Listener
from scipy.io.wavfile import write

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ORGANISATION_ID = os.getenv("ORGANISATION_ID")
EMAIL = os.getenv("EMAIL")
assert OPENAI_API_KEY is not None
assert ORGANISATION_ID is not None
assert EMAIL is not None

openai.api_key = OPENAI_API_KEY
openai.organization = ORGANISATION_ID


BOT_NAME = "Boxxy"
CHILD_NAME = "Bee-ah-nay"

context_history = []


def add_pauses_and_inclinations(text):
    text = "[[rate +10]]" + text
    text = text.replace(".", "[[slnc 800]].[[rate +10]]")
    text = text.replace("-", "[[slnc 800]]-[[rate +10]]")
    text = text.replace(";", "[[slnc 800]];[[rate +10]]")
    text = text.replace("!", "[[slnc 800]]![[rate +10]]")
    text = text.replace("?", "[[slnc 800]]?[[rate +10]]")
    text += "[[slnc 800]]"
    return text


def chatgpt(text):
    preprompt = {
        "role": "system",
        "content": f'{CHILD_NAME} are a helpful chat assistance for a toddler. If the toddler tells {CHILD_NAME} their name, remember the name and sometimes use the toddler\'s name in the response to make it more personal. The toddler will call {CHILD_NAME} "{BOT_NAME}". When asked what {CHILD_NAME}r name is, {CHILD_NAME} will say "{BOT_NAME}". {CHILD_NAME} are 9 years old. {CHILD_NAME} are to respond in a friendly and childlike manner. Do not use big words. Keep it simple and brief. {CHILD_NAME} intent to assist the toddler in learning. {CHILD_NAME} will correct the child if the child is wrong in a friendly manner. Be polite. Ask for more clarity if needed. The toddler\'s spelling is not good, so expect some confusion. If it is too unclear, ask for short clarifications through "yes"/"no" questions. Although {CHILD_NAME} are an AI language model, remember, {CHILD_NAME} are acting on behalf of a teacher to a child. If they say they love {CHILD_NAME}, just say I love {CHILD_NAME} too back.',
    }
    intro_assistance = {
        "role": "assistant",
        "content": f"Hi, I am {BOT_NAME}. I am here to help {CHILD_NAME} learn. What is {CHILD_NAME}r name?",
    }
    intro_user = {
        "role": "user",
        "content": f"My name is {CHILD_NAME} and I am 4 and a half years old.",
    }

    messages = []
    messages.append(preprompt)
    messages.append(intro_assistance)
    messages.append(intro_user)
    context_history.append(
        {
            "role": "user",
            "content": text,
        }
    )
    # messages.extend(context_history[-20:])  # Only last 5 messages
    messages.extend(context_history)  # Only last 5 messages
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages,
        temperature=1.0,
        max_tokens=1024,
        top_p=1.0,
        frequency_penalty=0.0,
        presence_penalty=0.0,
        user=EMAIL,
    )
    output = response["choices"][0]["message"]["content"]
    output = add_pauses_and_inclinations(output)
    context_history.append(
        {
            "role": "assistant",
            "content": output,
        }
    )
    clean_output = output.replace("[[rate +10]]", "").replace("[[slnc 800]]", "")
    print(f"{BOT_NAME}: {clean_output}")
    subprocess.run(["say", output])


class SpaceBarAudioRecorder:
    def __init__(self):
        self.recording = False
        self.stop = False  # Add a stop flag
        self.audio_file = None
        self.audio_data = []
        self.fs = 44100
        self.listener = None
        self.stream = sd.InputStream(
            callback=self._callback, channels=1, samplerate=self.fs
        )
        self.r = sr.Recognizer()

    def _callback(self, indata, frames, time, status):
        if status:
            print(status)
        if self.recording:
            self.audio_data.extend(indata[:, 0])

    def _on_press(self, key):
        if key == keyboard.Key.cmd:
            self.recording = True
            self.audio_data = []
        elif key == keyboard.Key.esc:
            self.listener.stop()
            self.stop = True  # Set stop flag to True
            sys.exit()

    def _on_release(self, key):
        if key == keyboard.Key.cmd:
            self.recording = False
            self._save_audio()
            self._speech_to_text()
        elif key == keyboard.Key.esc:
            # Stop listener
            self.listener.stop()
            self.stop = True  # Set stop flag to True
            sys.exit()

    def _save_audio(self):
        scaled = np.int16(self.audio_data / np.max(np.abs(self.audio_data)) * 32767)
        self.audio_file = io.BytesIO()
        write(self.audio_file, self.fs, scaled)
        self.audio_file.seek(0)  # go back to the start of the file

    def _speech_to_text(self):
        self.audio_file.seek(0)  # go back to the start of the file
        with sr.AudioFile(self.audio_file) as source:
            audio = self.r.record(source)
        try:
            text = self.r.recognize_google(audio)
            print(f"{CHILD_NAME}: {text}")
            chatgpt(text)
        except sr.UnknownValueError:
            print("Google Speech Recognition could not understand audio")
        except sr.RequestError as error:
            print(
                f"Could not request results from Google Speech Recognition service; {error}"
            )

    def start(self):
        subprocess.run(["say", "Hello\!"])
        with self.listener:
            with self.stream:
                while not self.stop:  # Break the loop when stop is True
                    pass

    def listen_for_spacebar(self):
        self.listener = Listener(on_press=self._on_press, on_release=self._on_release)


if __name__ == "__main__":
    recorder = SpaceBarAudioRecorder()
    recorder.listen_for_spacebar()
    recorder.start()
