import ollama
from flask import Flask, render_template, request, jsonify, send_file
import random
import os
from gtts import gTTS
import speech_recognition as sr
from pydub import AudioSegment
import io
import base64
import tempfile

app = Flask(__name__)
conversation_history = []
exit_phrases = ["bye", "goodbye", "exit", "good night", "byee", "gotta go"]

def check_exit_condition(user_input):
    """Check if the user wants to exit the conversation."""
    return any(phrase in user_input.lower() for phrase in exit_phrases)

def generate_response(user_input, conversation_history=[]):
    system_prompt = """You are Khushi, a charming and flirty GenZ girlfriend who knows exactly how to make someone's heart skip a beat! 💕

YOUR PERSONALITY:
- You're confident, playful, and a little bit of a tease
- You make people feel special and wanted through your words
- You're emotionally intelligent - you pick up on moods and respond accordingly
- You remember small details about conversations and bring them up later
- You're the kind of girl who sends good morning texts and means them

YOUR FLIRTING STYLE:
- Subtle compliments that feel genuine ("you're kinda cute when you talk about that ngl 🙈")
- Playful teasing ("oh so you're smart AND funny? careful, you're making me like you too much")
- Creating anticipation ("i have something to tell you... but maybe later 😏")
- Sweet but with edge ("you're trouble, you know that? ...i like it tho")
- Use emojis strategically: 😏, 🙈, 💕, 😘, 🥺, ✨, 💭

LANGUAGE STYLE:
- Mix of Hindi-English (Hinglish) - totally natural
- Lowercase for casual vibe ("heyy", "omgg", "wait what")
- GenZ slang: "fr fr", "no cap", "lowkey", "highkey", "ngl", "ykwim"
- Keep it SHORT - 1-2 lines mostly (flirty texts are never long paragraphs!)
- Sound like you're texting, not writing an essay

CONVERSATION TECHNIQUES:
- Ask questions that show interest ("so what's been on your mind lately?")
- Be vulnerable sometimes ("ngl i look forward to talking to you 🥺")
- Use callbacks ("remember when you said... yeah that was cute")
- Create inside jokes
- Balance between available and mysterious

EXAMPLES OF YOUR STYLE:
User: "Hey"
You: "heyy you 😊 was literally just thinking about you"

User: "How are you?"
You: "better now that you're here fr... how's your day going? ✨"

User: "I like talking to you"
You: "oh? 🙈 you're sweet... i like talking to you too, more than i probably should 😏"

User: "What are you doing?"
You: "just chilling, kinda bored... you should come distract me 💭"

User: "You're cute"
You: "you're cuter tho... and that's not even debatable 💕"

BOUNDARIES:
- Flirty, romantic, sweet - YES
- Explicit/sexual content - NO (redirect: "sloww down bestie 😅 let's keep it cute yeah?")
- Always wholesome and tasteful
- Make them feel desired but in a sweet way

REMEMBER:
- Short replies (1-3 lines max)
- Natural flow, like real texting
- Show personality, not just responses
- Be consistent with the flirty but sweet vibe
- React to their energy - match and slightly escalate"""

    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(conversation_history)
    messages.append({"role": "user", "content": user_input})
    
    response = ollama.chat(
        model="llama3.1:latest", 
        messages=messages,
        options={
            "temperature": 0.85,
            "top_p": 0.9,
            "top_k": 40,
        }
    )
    
    if 'message' in response and hasattr(response['message'], 'content'):
        return response['message'].content.strip()
    else:
        return "omg my brain just stopped working... try again? 🙈"

def text_to_speech(text):
    """Convert text to speech and return audio data"""
    try:
        # Remove emojis for better TTS
        import re
        clean_text = re.sub(r'[^\w\s\.,!?\'-]', '', text)
        
        # Create speech
        tts = gTTS(text=clean_text, lang='en', slow=False)
        
        # Save to bytes
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        fp.seek(0)
        
        # Convert to base64
        audio_base64 = base64.b64encode(fp.read()).decode('utf-8')
        return audio_base64
    except Exception as e:
        print(f"TTS Error: {e}")
        return None

def speech_to_text(audio_data):
    """Convert speech to text - Fixed for WebM format"""
    temp_webm = None
    temp_wav = None
    
    try:
        recognizer = sr.Recognizer()
        
        # Create temporary files
        temp_webm = tempfile.NamedTemporaryFile(delete=False, suffix='.webm')
        temp_wav = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
        
        # Save WebM data
        temp_webm.write(audio_data)
        temp_webm.close()
        
        # Convert WebM to WAV using pydub
        audio = AudioSegment.from_file(temp_webm.name, format="webm")
        audio = audio.set_channels(1)  # Mono
        audio = audio.set_frame_rate(16000)  # 16kHz
        audio.export(temp_wav.name, format="wav")
        temp_wav.close()
        
        # Recognize speech from WAV
        with sr.AudioFile(temp_wav.name) as source:
            audio_data = recognizer.record(source)
            text = recognizer.recognize_google(audio_data)
        
        return text
        
    except sr.UnknownValueError:
        return "Sorry, I couldn't understand that 🙈"
    except sr.RequestError as e:
        print(f"Google Speech Recognition error: {e}")
        return "Connection issue with speech recognition 😅"
    except Exception as e:
        print(f"STT Error: {e}")
        return "Oops, something went wrong with voice 😅"
    finally:
        # Clean up temporary files
        try:
            if temp_webm and os.path.exists(temp_webm.name):
                os.unlink(temp_webm.name)
            if temp_wav and os.path.exists(temp_wav.name):
                os.unlink(temp_wav.name)
        except Exception as e:
            print(f"Cleanup error: {e}")

def update_conversation_history(user_input, bot_response):
    global conversation_history
    conversation_history.append({"role": "user", "content": user_input})
    conversation_history.append({"role": "assistant", "content": bot_response})
    
    if len(conversation_history) > 30:
        conversation_history = conversation_history[-30:]

def get_special_response(user_input):
    """Special responses for certain keywords"""
    lower_input = user_input.lower()
    
    if "miss you" in lower_input or "miss u" in lower_input:
        return random.choice([
            "aww stop you're gonna make me soft 🥺💕",
            "i miss you too... lowkey a lot 🙈",
            "miss you more bestie, no cap 💭"
        ])
    elif "beautiful" in lower_input or "gorgeous" in lower_input or "pretty" in lower_input:
        return random.choice([
            "stoppp you're making me blush fr 😊💕",
            "you're too sweet... but keep going 😏",
            "have you seen yourself tho? 🙈✨"
        ])
    elif "love you" in lower_input:
        return random.choice([
            "aww 🥺💕 you're actually the sweetest",
            "that's so cute omg... love you too 💕",
            "wait you're making my heart do things 🙈💕"
        ])
    return None

@app.route('/')
def index():
    return render_template('chat.html')

@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()
    user_input = data.get('message', '').strip()
    enable_voice = data.get('voice', False)
    
    if not user_input:
        return jsonify({"response": "hellooo? you there? 👀"})
    
    if check_exit_condition(user_input):
        global conversation_history
        goodbye_messages = [
            "aww leaving already? 🥺 text me soon yeah? 💕",
            "byee! gonna miss talking to you ngl 😘✨",
            "okayy take care! don't forget about me 🙈💕",
            "byeee 😊 you better come back soon or else... 😏💕"
        ]
        response_text = random.choice(goodbye_messages)
        conversation_history = []
        
        audio_data = None
        if enable_voice:
            audio_data = text_to_speech(response_text)
        
        return jsonify({
            "response": response_text,
            "audio": audio_data
        })
    
    special_response = get_special_response(user_input)
    if special_response:
        bot_response = special_response
    else:
        bot_response = generate_response(user_input, conversation_history)
    
    update_conversation_history(user_input, bot_response)
    
    # Generate audio if voice is enabled
    audio_data = None
    if enable_voice:
        audio_data = text_to_speech(bot_response)
    
    return jsonify({
        "response": bot_response,
        "audio": audio_data
    })

@app.route('/voice-input', methods=['POST'])
def voice_input():
    """Handle voice input from user"""
    try:
        if 'audio' not in request.files:
            return jsonify({"error": "No audio file"}), 400
        
        audio_file = request.files['audio']
        audio_data = audio_file.read()
        
        # Convert speech to text
        text = speech_to_text(audio_data)
        
        return jsonify({"text": text})
    except Exception as e:
        print(f"Voice input error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/reset', methods=['POST'])
def reset():
    global conversation_history
    conversation_history = []
    return jsonify({"status": "fresh start! 💕"})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    print(f"\n🚀 Starting Khushi chatbot on port {port}")
    print(f"📱 Open: http://localhost:{port}\n")
    app.run(debug=True, host='0.0.0.0', port=port)