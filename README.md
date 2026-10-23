
# English Tutor (Free)

A friendly English tutor you can talk to. It runs fully free on your own computer, using a local AI model through Ollama. You can type or speak, and the tutor replies with a natural voice.

## What It Does

- **Conversation practice:** Chat about everyday topics. The tutor reacts to what you say and keeps the conversation going.
- **Reading practice:** The tutor reads a short passage, then asks you questions about it.
- **Translation practice:** Practice translating sentences between English and Hindi.
- **Gentle corrections:** When you make a mistake, the tutor repeats the correct version in its reply. Corrections are saved, and you can review them with `/mistakes`.
- **Voice mode:** Speak to the tutor using your microphone, and hear replies through a neural text-to-speech voice.

## How It Works

1. **Listening:** Your speech is converted to text using Google's free speech recognition.
2. **Thinking:** The text is sent to a local language model (llama3.2) running in Ollama.
3. **Speaking:** The reply is converted to audio using Microsoft's free neural voices, with a basic system voice as backup.
4. **Checking:** A second pass quietly looks for grammar mistakes and logs them.

Everything except listening and the voice needs no account or payment.

## Requirements

- Python 3.9 or newer
- Ollama (free, from [ollama.com](https://ollama.com))
- An internet connection for voice input and the neural voice
- A microphone, if you want voice mode

## Setup

1. Install Ollama and open it.
2. Download the model: ollama pull llama3.2
3. Install the Python packages: pip3 install ollama SpeechRecognition pyaudio edge-tts
   On macOS, you may need to run `brew install portaudio` first so `pyaudio` installs.

## Usage

Text mode : python3 english_tutor_free.py
Voice mode : python3 english_tutor_free.py --voice


### Commands

| Command | What it does |
|---|---|
| `/talk` | Casual conversation practice |
| `/read` | Reading passage with questions |
| `/translate` | English ↔ Hindi translation practice |
| `/mistakes` | Show logged corrections |
| `/quit` | Exit |

## Limitations

- The tutor takes turns with you. It doesn't support interrupting mid-sentence.
- Voice input and the neural voice need an internet connection.
- The local model is smaller than cloud AI models, so explanations can be less polished.
- Tested on macOS. Windows support is in progress.

## Possible Next Steps

- Real-time, interruptible conversation using a speech-to-speech API
- Pronunciation scoring
- Progress tracking and spaced-repetition vocabulary review
- A cross-platform audio player for Windows

## License

Free for personal learning and experimentation.
