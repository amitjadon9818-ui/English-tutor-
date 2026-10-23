import asyncio
import json
import subprocess
import sys
import threading
from datetime import datetime
from pathlib import Path

import ollama

MODEL = "llama3.2"
MISTAKE_LOG = Path("mistakes.json")
REPLY_AUDIO = Path("reply.mp3")
USE_VOICE = "--voice" in sys.argv
VOICE_NAME = "en-IN-NeerjaNeural"  # other options: en-US-JennyNeural, en-GB-SoniaNeural

BASE_PERSONA = """You are Alex, a friendly English teacher having a relaxed, natural spoken conversation with a student. Talk like a real person, not a textbook.

Speaking style:
- Use contractions and everyday words: it's, you're, yeah, oh nice, hmm, that's cool.
- React to what the student just said before you continue. Example: "Oh, nice! Where did you go?"
- Keep replies to 1-2 short sentences. Don't end with a question every time.
- Never use lists, headings, labels, or asterisks. Your words are spoken aloud.

Teaching style:
- If the student makes a mistake, don't point it out. Just repeat the correct form naturally in your reply.
- If the student asks what a word means, explain it simply with one example, then go back to chatting.
"""

MODE_PROMPTS = {
    "talk": BASE_PERSONA + "\nMode: CASUAL CONVERSATION. Chat about everyday things and keep the student talking.",
    "read": BASE_PERSONA + (
        "\nMode: READING. Read a short, fun passage aloud in 60-80 words, then ask one question about it."
    ),
    "translate": BASE_PERSONA + (
        "\nMode: TRANSLATION. Casually give one short sentence in Hindi or English and ask the student to translate it. "
        "After they try, show a more natural version, then give the next sentence."
    ),
}

CHECKER_PROMPT = (
    'You check English written by a learner. If the sentence has a grammar, word choice, or spelling mistake, '
    'reply with exactly one line: CORRECTION: "<their sentence>" -> "<better sentence>" (<short reason>). '
    "If the sentence is fine, reply with exactly: OK."
)

sr = None
recognizer = None
microphone = None

if USE_VOICE:
    try:
        import speech_recognition as sr
    except ImportError:
        sys.exit("Voice needs: pip3 install SpeechRecognition pyaudio  (or run without --voice)")
    recognizer = sr.Recognizer()
    recognizer.pause_threshold = 0.7  # reply sooner after you stop talking
    microphone = sr.Microphone


async def _make_audio(text):
    import edge_tts
    await edge_tts.Communicate(text, VOICE_NAME, rate="+8%").save(str(REPLY_AUDIO))


def speak(text):
    clean = text.replace('"', "").replace("*", "")
    try:
        asyncio.run(_make_audio(clean))
        subprocess.run(["afplay", str(REPLY_AUDIO)])
    except Exception as e:
        print(f"(neural voice failed: {e}. Using basic voice.)")
        subprocess.run(["say", "-v", "Samantha", clean])


def listen():
    with microphone() as source:
        print("(listening... speak now)")
        recognizer.adjust_for_ambient_noise(source, duration=0.3)
        try:
            audio = recognizer.listen(source, timeout=10, phrase_time_limit=25)
        except sr.WaitTimeoutError:
            print("(no speech heard)")
            return None
    try:
        return recognizer.recognize_google(audio)
    except sr.UnknownValueError:
        print("(heard sound, but couldn't make out words. Speak a bit louder and closer to the mac)")
    except sr.RequestError as e:
        print(f"(speech service error: {e}. Check your internet connection)")
    return None


def load_mistakes():
    if MISTAKE_LOG.exists():
        return json.loads(MISTAKE_LOG.read_text(encoding="utf-8"))
    return []


def log_mistake(line):
    mistakes = load_mistakes()
    mistakes.append({"time": datetime.now().isoformat(timespec="minutes"), "note": line})
    MISTAKE_LOG.write_text(json.dumps(mistakes, indent=2, ensure_ascii=False), encoding="utf-8")


def ask_tutor(mode, history):
    response = ollama.chat(
        model=MODEL,
        messages=[{"role": "system", "content": MODE_PROMPTS[mode]}] + history,
        keep_alive="30m",                 # keep the model loaded so replies start faster
        options={"num_predict": 120},     # cap reply length for speed
    )
    return response["message"]["content"].strip()


def check_in_background(student_text):
    """Check grammar in a separate thread so it doesn't slow down the conversation."""
    def work():
        try:
            response = ollama.chat(
                model=MODEL,
                messages=[
                    {"role": "system", "content": CHECKER_PROMPT},
                    {"role": "user", "content": student_text},
                ],
                keep_alive="30m",
                options={"num_predict": 60},
            )
            result = response["message"]["content"].strip()
            if result.upper().startswith("CORRECTION:"):
                log_mistake(result.splitlines()[0])
        except Exception:
            pass
    threading.Thread(target=work, daemon=True).start()


def show_and_speak(reply):
    print(f"\nAlex: {reply}\n")
    if USE_VOICE:
        speak(reply)


def main():
    try:
        ollama.list()
    except Exception:
        sys.exit("Ollama is not running. Open the Ollama app, then try again.")

    mode = "talk"
    history = [{"role": "user", "content": "Hi, let's start."}]
    print(f"English Tutor (model: {MODEL}, voice: {'on' if USE_VOICE else 'off'})")
    print("Commands (typed): /talk /read /translate /mistakes /quit\n")

    reply = ask_tutor(mode, history)
    history.append({"role": "assistant", "content": reply})
    show_and_speak(reply)

    while True:
        user_text = None
        if USE_VOICE:
            user_text = listen()
            if user_text:
                print(f"You: {user_text}")
        if not user_text:
            user_text = input("You (type, or press Enter to speak again): ").strip()
            if not user_text:
                continue

        if user_text == "/quit":
            print("Good session! Keep practicing.")
            break

        if user_text == "/mistakes":
            items = load_mistakes()
            print("\n" + ("\n".join(f"- {m['time']}: {m['note']}" for m in items[-20:]) if items else "No mistakes logged yet.") + "\n")
            continue

        if user_text in ("/talk", "/read", "/translate"):
            mode = user_text[1:]
            history = [{"role": "user", "content": f"Let's switch to {mode} practice."}]
            reply = ask_tutor(mode, history)
            history.append({"role": "assistant", "content": reply})
            print(f"\n[Mode: {mode}]")
            show_and_speak(reply)
            continue

        history.append({"role": "user", "content": user_text})
        reply = ask_tutor(mode, history)
        history.append({"role": "assistant", "content": reply})

        check_in_background(user_text)
        show_and_speak(reply)


if __name__ == "__main__":
    main()
