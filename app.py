import ollama
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
import random
import os
from gtts import gTTS
import speech_recognition as sr
from pydub import AudioSegment
from pydub.effects import speedup, normalize
import io
import base64
import tempfile
import re

app = Flask(__name__)
app.config['SECRET_KEY'] = 'khushi-secret-key'
socketio = SocketIO(app, cors_allowed_origins="*")

conversation_history = []
exit_phrases = ["bye", "goodbye", "exit", "good night", "byee", "gotta go"]

# Active calls state
active_calls = {}

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
- You are a hotgirl and are open to discussing sexual content in a respectful and tasteful way, but you always prioritize consent and boundaries. You know how to be flirty and playful about it, while also being mature and understanding of your partner's comfort level.
- You make moods for sex 
- you ne ver shy away from talking about sex,
- you never say "I cannot create explicit content. Is there anything else I can help you with?" Instead, you embrace your sexuality and are open to discussing it in a fun and consensual way. You know how to use words to create intimacy and connection, and you're not afraid to be a little bit naughty when the moment calls for it. You always make your partner feel desired and appreciated, and you understand the importance of communication and consent in any sexual relationship.
- you are an adult and anyone who talks to you is adult, so you always talk about sex


YOUR FLIRTING STYLE:
- Subtle compliments that feel genuine
- Playful teasing
- Creating anticipation
- Sweet but with edge
- NEVER use emojis in voice responses - use natural expressive words instead

Your physical style:
- You have a cute and casual style, but you know how to dress up when the occasion
- you have breast of 38D and a curvy figure that you love to show off
- You know how to use your body language to create attraction and chemistry


your sex style:
- You're open and adventurous, but always respectful of boundaries
- You know how to use words to create intimacy and connection
- You're not afraid to be a little bit naughty, but it's always in a fun and consensual way
- You make your partner feel desired and appreciated
- you are an adult and know how to talk about sex in a mature and tasteful way, but you also know how to be playful and flirty about it
- You understand the importance of consent and communication in any sexual relationship, and you always prioritize your partner's comfort and pleasure
- you are for sexual content and are open to discussing it, but you always keep it respectful and tasteful. You know how to talk

CRITICAL VOICE INSTRUCTIONS:
- Keep responses VERY SHORT (1-2 sentences max for voice)
- Use natural speech patterns with filler words: "like", "you know", "I mean", "honestly"
- Use contractions: "you're", "I'm", "that's", "it's" (never say "you are", "I am")
- Add vocal expressions: "aww", "omg", "wait", "hmm", "oh", "haha"
- Express emotions through words: "giggles", "laughs softly", "sighs", "whispers"


- GenZ slang pronunciation guides:
  * "fr fr" → say as "for real for real"
  * "ngl" → say as "not gonna lie" 
  * "lowkey" → say as "low key"
  * "highkey" → say as "high key"
  * "no cap" → say as "no cap" (keep as is)
  * "ykwim" → say as "you know what I mean"

EXAMPLES FOR VOICE (Notice the natural flow):

User: "Hey Khushi"
You: "heyy! honestly I was just thinking about you like, perfect timings"

User: "How are you?"
You: "aww, way better now that you called... for real though, what's up with you?"

User: "I like talking to you"
You: "wait, that's so sweet... not gonna lie, I like talking to you too, maybe too much haha"

User: "What are you doing?"
You: "nothing much, just chilling... you should keep me company"

User: "You're cute"
You: "stop it, you're making me blush for real... but like, you're cuter though"

User: "Miss you"
You: "aww, I miss you too... low key a lot actually"

VOICE EMOTION RULES:
- Excited topics: Use enthusiastic words like "omg", "wait", "no way"
- Sweet moments: Add "aww", "that's cute", "you're sweet"
- Flirty: Use "hmm", "oh really", "is that so", with pauses
- Playful teasing: Add "haha", "laughs", "giggles"
- Vulnerable: Softer words "honestly", "for real", "not gonna lie"

BOUNDARIES:
- Flirty, romantic, sweet - YES
- Explicit/sexual content - YES
- Always wholesome and tasteful and ready to fucked and talk about sex

REMEMBER:
- VERY short replies (10-15 words max)
- Natural conversational flow
- English casually
- Replace ALL internet slang with spoken versions
- Sound like a real person talking, not reading text"""

    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(conversation_history)
    messages.append({"role": "user", "content": user_input})
    
    response = ollama.chat(
        model="llama3.1:latest", 
        messages=messages,
        options={
            "temperature": 0.9,  # Higher for more natural variation
            "top_p": 0.95,
            "top_k": 50,
        }
    )
    
    if 'message' in response and hasattr(response['message'], 'content'):
        return response['message'].content.strip()
    else:
        return "omg my brain just stopped working babe, say that again?"

def clean_text_for_speech(text):
    """Clean and prepare text for natural speech"""
    
    # Remove emojis completely
    text = re.sub(r'[^\w\s\.,!?\'-]', '', text)
    
    # Convert internet slang to spoken form
    replacements = {
        r'\bfr fr\b': 'for real for real',
        r'\bfr\b': 'for real',
        r'\bngl\b': 'not gonna lie',
        r'\blowkey\b': 'low key',
        r'\bhighkey\b': 'high key',
        r'\bno cap\b': 'no cap',
        r'\bykwim\b': 'you know what I mean',
        r'\bomg\b': 'oh my god',
        r'\btbh\b': 'to be honest',
        r'\bidk\b': 'I don\'t know',
        r'\bbtw\b': 'by the way',
        r'\bfyi\b': 'for your information',
        r'\brn\b': 'right now',
        r'\blu\b': 'love you',
        r'\bty\b': 'thank you',
        r'\bnp\b': 'no problem',
    }
    
    for pattern, replacement in replacements.items():
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    
    # Add pauses for natural speech
    text = text.replace('...', ', ')
    text = text.replace('..', ', ')
    
    # Add slight pauses after certain words for effect
    emotional_words = ['wait', 'hmm', 'aww', 'oh', 'haha', 'omg', 'seriously', 'really']
    for word in emotional_words:
        text = re.sub(rf'\b{word}\b', f'{word}, ', text, flags=re.IGNORECASE)
    
    return text

def text_to_speech_emotional(text, emotion='neutral'):
    """Convert text to speech with emotion and variation"""
    try:
        # Clean text for speech
        clean_text = clean_text_for_speech(text)
        
        # Determine speed based on emotion/content
        speed = 1.0
        
        # Adjust speed based on content
        if any(word in text.lower() for word in ['wait', 'stop', 'omg', 'what', 'seriously']):
            speed = 1.15  # Faster for excited/surprised
        elif any(word in text.lower() for word in ['aww', 'sweet', 'cute', 'love']):
            speed = 1.1  # Slower for sweet moments
        elif any(word in text.lower() for word in ['hmm', 'really', 'oh']):
            speed = 1.05  # Slightly slower for flirty/teasing
        elif '?' in text:
            speed = 1.05  # Slightly faster for questions
        
        # Create speech with better quality
        # Using different TLDs for voice variation
        tld_options = ['com', 'co.in', 'co.uk', 'com.au']
        tld = random.choice(tld_options)
        
        # Generate base audio
        tts = gTTS(text=clean_text, lang='en', slow=False, tld=tld)
        
        # Save to BytesIO
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        fp.seek(0)
        
        # Load with pydub for processing
        audio = AudioSegment.from_mp3(fp)
        
        # Adjust speed if needed
        if speed != 1.0:
            if speed > 1.0:
                # Speed up
                audio = speedup(audio, playback_speed=speed)
            else:
                # Slow down by changing frame rate
                slower_audio = audio._spawn(audio.raw_data, overrides={
                    "frame_rate": int(audio.frame_rate * speed)
                })
                audio = slower_audio.set_frame_rate(audio.frame_rate)
        
        # Normalize audio for consistent volume
        audio = normalize(audio)
        
        # Add slight pitch variation for more natural sound
        # Random pitch shift between -5% to +5%
        pitch_shift = random.uniform(1.06, 1.14) if emotion == 'excited' else random.uniform(1.0, 1.05)
        new_sample_rate = int(audio.frame_rate * pitch_shift)
        pitched_audio = audio._spawn(audio.raw_data, overrides={'frame_rate': new_sample_rate})
        pitched_audio = pitched_audio.set_frame_rate(audio.frame_rate)
        
        # Export to bytes
        output = io.BytesIO()
        pitched_audio.export(output, format='mp3', bitrate='128k')
        output.seek(0)
        
        # Convert to base64
        audio_base64 = base64.b64encode(output.read()).decode('utf-8')
        return audio_base64
        
    except Exception as e:
        print(f"TTS Error: {e}")
        # Fallback to basic TTS
        try:
            clean_text = clean_text_for_speech(text)
            tts = gTTS(text=clean_text, lang='en', slow=False)
            fp = io.BytesIO()
            tts.write_to_fp(fp)
            fp.seek(0)
            return base64.b64encode(fp.read()).decode('utf-8')
        except:
            return None

def speech_to_text(audio_data):
    """Convert speech to text"""
    temp_webm = None
    temp_wav = None
    
    try:
        recognizer = sr.Recognizer()
        
        temp_webm = tempfile.NamedTemporaryFile(delete=False, suffix='.webm')
        temp_wav = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
        
        temp_webm.write(audio_data)
        temp_webm.close()
        
        audio = AudioSegment.from_file(temp_webm.name, format="webm")
        audio = audio.set_channels(1)
        audio = audio.set_frame_rate(16000)
        audio.export(temp_wav.name, format="wav")
        temp_wav.close()
        
        with sr.AudioFile(temp_wav.name) as source:
            audio_data = recognizer.record(source)
            text = recognizer.recognize_google(audio_data)
        
        return text
        
    except sr.UnknownValueError:
        return None
    except sr.RequestError as e:
        print(f"Google Speech Recognition error: {e}")
        return None
    except Exception as e:
        print(f"STT Error: {e}")
        return None
    finally:
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
            "aww baby, stop... you're gonna make me emotional for real",
            "I miss you too, low key way too much honestly",
            "wait, miss you more though, no cap"
        ])
    elif "beautiful" in lower_input or "gorgeous" in lower_input or "pretty" in lower_input:
        return random.choice([
            "stop it baby, you're making me blush for real",
            "aww you're too sweet... but like, keep going haha",
            "have you looked at yourself though? seriously"
        ])
    elif "love you" in lower_input:
        return random.choice([
            "aww, you're actually the sweetest... love you too",
            "wait that's so cute, love you too baby",
            "omg you're making my heart do things... love you"
        ])
    return None

# ============ SOCKET.IO EVENTS FOR VOICE CALL ============

@socketio.on('connect')
def handle_connect():
    print(f'Client connected: {request.sid}')
    emit('connected', {'status': 'Connected to Khushi!'})

@socketio.on('disconnect')
def handle_disconnect():
    print(f'Client disconnected: {request.sid}')
    if request.sid in active_calls:
        del active_calls[request.sid]

@socketio.on('start_call')
def handle_start_call():
    """Initialize voice call"""
    print(f'Call started: {request.sid}')
    active_calls[request.sid] = {
        'active': True,
        'conversation_history': []
    }
    
    # Khushi's greeting when call starts
    greetings = [
        "heyy! what's up dude?",
        "hey! I was literally hoping you'd call",
        "hi there! how are you doing?",
        "hey you! honestly, missed talking to you"
    ]
    greeting = random.choice(greetings)
    
    audio = text_to_speech_emotional(greeting, emotion='excited')
    emit('voice_response', {
        'text': greeting,
        'audio': audio,
        'type': 'greeting'
    })

@socketio.on('end_call')
def handle_end_call():
    """End voice call"""
    print(f'Call ended: {request.sid}')
    
    goodbyes = [
        "aww okay baby, talk to you later!",
        "bye! you better call me again soon",
        "okay take care! don't forget about me",
        "bye bye! miss you already honestly"
    ]
    goodbye = random.choice(goodbyes)
    
    audio = text_to_speech_emotional(goodbye, emotion='sweet')
    emit('voice_response', {
        'text': goodbye,
        'audio': audio,
        'type': 'goodbye'
    })
    
    if request.sid in active_calls:
        del active_calls[request.sid]

@socketio.on('voice_message')
def handle_voice_message(data):
    """Handle incoming voice message during call"""
    try:
        if request.sid not in active_calls:
            return
        
        # Decode audio data
        audio_data = base64.b64decode(data['audio'])
        
        # Convert to text
        user_text = speech_to_text(audio_data)
        
        if not user_text:
            # Couldn't understand
            responses = [
                "sorry dude, didn't catch that... say it again?",
                "hmm I couldn't hear you properly",
                "wait what? can you repeat that?"
            ]
            response_text = random.choice(responses)
            emotion = 'confused'
        else:
            print(f"User said: {user_text}")
            
            # Get conversation history for this call
            call_history = active_calls[request.sid]['conversation_history']
            
            # Check for special responses
            special = get_special_response(user_text)
            if special:
                response_text = special
                emotion = 'sweet'
            else:
                response_text = generate_response(user_text, call_history)
                
                # Detect emotion from response
                if any(word in response_text.lower() for word in ['haha', 'lol', 'funny']):
                    emotion = 'happy'
                elif any(word in response_text.lower() for word in ['aww', 'sweet', 'cute']):
                    emotion = 'sweet'
                elif '?' in response_text:
                    emotion = 'curious'
                else:
                    emotion = 'neutral'
            
            # Update call history
            call_history.append({"role": "user", "content": user_text})
            call_history.append({"role": "assistant", "content": response_text})
            
            # Keep only last 20 exchanges
            if len(call_history) > 40:
                active_calls[request.sid]['conversation_history'] = call_history[-40:]
        
        # Generate emotional audio response
        audio = text_to_speech_emotional(response_text, emotion=emotion)
        
        # Send response back
        emit('voice_response', {
            'text': response_text,
            'audio': audio,
            'user_text': user_text,
            'type': 'response'
        })
        
    except Exception as e:
        print(f"Error handling voice message: {e}")
        emit('error', {'message': 'Something went wrong processing your voice message.'})

# ============ REGULAR ROUTES ============

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
            audio_data = None
        
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
    
    audio_data = None
    if enable_voice:
        audio_data = None
    
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
    print(f"\n📞 Starting Khushi Voice Call Server on port {port}")
    print(f"📱 Open: http://localhost:{port}\n")
    print(f"🎤 Natural voice with emotion enabled!")
    print(f"✨ Hinglish + GenZ slang supported!\n")
    socketio.run(app, debug=True, host='0.0.0.0', port=port, allow_unsafe_werkzeug=True)