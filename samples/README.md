# Voice Email Demo Samples

This folder contains audio samples for testing the voice email feature.

## How to Create a Demo Recording

1. **Record a short audio** (10-30 seconds) on your phone or computer
2. **Save it as** MP3, WAV, M4A, or any supported format
3. **Place it in this folder**

### Example Script to Record

Say something like:

> "Hey, I need to send an email to John at Acme Corp about the project deadline. 
> Let him know we're on track to deliver by Friday, and ask if he can review 
> the budget proposal I sent last week. Thanks!"

### Supported Formats

- WAV
- MP3
- M4A
- AIFF
- AAC
- OGG
- FLAC

## Testing the Voice Feature

```bash
# From the mailAgent directory
python cli.py voice samples/your-recording.mp3

# With recipient hint
python cli.py voice samples/your-recording.mp3 --to john@acme.com
```

## What the Agent Does

1. Transcribes your audio using Gemini
2. Extracts recipient and intent
3. Researches the recipient if corporate email
4. Generates a polished email draft
5. Asks for confirmation before sending
