"""
Voice-activated unlock example.

Listens for the phrase "unlock computer" using the SpeechRecognition
library, then sends an UNLOCK command to the credential provider.

Requirements:
    pip install SpeechRecognition pyaudio

Usage:
    python example_voice.py <username> <password> [domain]
"""

import sys
import speech_recognition as sr
from credential_provider import CredentialProviderClient


def voice_unlock(username: str, password: str, domain: str = ".") -> None:
    client = CredentialProviderClient()
    recognizer = sr.Recognizer()
    mic = sr.Microphone()

    print("Adjusting for ambient noise...")
    with mic as source:
        recognizer.adjust_for_ambient_noise(source, duration=1)

    print('Listening. Say "unlock computer" to unlock the workstation.')

    while True:
        with mic as source:
            audio = recognizer.listen(source, phrase_time_limit=5)

        try:
            text = recognizer.recognize_google(audio).lower()
            print(f"Heard: {text}")
        except sr.UnknownValueError:
            continue
        except sr.RequestError as exc:
            print(f"Speech API error: {exc}")
            continue

        if "unlock" in text:
            print("Voice command matched. Sending unlock...")
            result = client.unlock_with_retry(username, password, domain)
            print(f"Result: {result.response}")
            if result.success:
                break
            print("Unlock was not successful. Listening again...")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python example_voice.py <username> <password> [domain]")
        sys.exit(1)
    voice_unlock(
        sys.argv[1],
        sys.argv[2],
        sys.argv[3] if len(sys.argv) > 3 else ".",
    )
