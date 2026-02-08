import ollama
from flask import Flask, render_template, request, jsonify
import random

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
            "temperature": 0.85,  # More creative and playful
            "top_p": 0.9,
            "top_k": 40,
        }
    )
    
    if 'message' in response and hasattr(response['message'], 'content'):
        return response['message'].content.strip()
    else:
        return "omg my brain just stopped working... try again? 🙈"

def update_conversation_history(user_input, bot_response):
    global conversation_history
    conversation_history.append({"role": "user", "content": user_input})
    conversation_history.append({"role": "assistant", "content": bot_response})
    
    # Keep last 15 exchanges for better context
    if len(conversation_history) > 30:
        conversation_history = conversation_history[-30:]

# Fun reactions for specific keywords
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
        conversation_history = []
        return jsonify({"response": random.choice(goodbye_messages)})
    
    # Check for special responses first
    special_response = get_special_response(user_input)
    if special_response:
        bot_response = special_response
    else:
        bot_response = generate_response(user_input, conversation_history)
    
    update_conversation_history(user_input, bot_response)
    
    return jsonify({"response": bot_response})

@app.route('/reset', methods=['POST'])
def reset():
    global conversation_history
    conversation_history = []
    return jsonify({"status": "fresh start! 💕"})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)