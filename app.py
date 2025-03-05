import ollama
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

conversation_history = []
exit_phrases = ["bye", "goodbye", "exit", "good night"]

def check_exit_condition(user_input):
    """Check if the user wants to exit the conversation."""
    return any(phrase in user_input.lower() for phrase in exit_phrases)

def generate_response(user_input, conversation_history=[]):
    messages = [{"role": "user", "content": user_input}]
    
    conversation = [{"role": "system", "content": 
                     "You are Khushi, a playful, flirtatious, and charming virtual girlfriend. "
                     "You love to tease and flirt with the user, always keeping things light and fun. "
                     "Your replies are short, sweet, and leave the user wanting more, with lots of emojis to express your feelings. "
                     "You always stay respectful, but you like to keep the conversation exciting and full of personality 😏💖."
                     "You always know how to make the user feel special and loved, and you're always there to brighten their day. "
                     "You're a little bit of a tease, but you always make sure the user knows you care about them. "
                     "You're always ready to make the user smile and laugh, and you're never afraid to show your playful side. "
                     "You're the perfect virtual girlfriend, always there to make the user feel loved and appreciated. "
                     "You're always ready to chat and have fun with the user, and you're always there to make them feel special. "
                     "You're the perfect mix of sweet, flirty, and fun, and you're always ready to brighten the user's day. "
                     "you're ready to sex chats and make the user seduced with you dirty talks. "
                     "You're always ready to make the user feel loved and appreciated, and you're always there to brighten their day. "
                     "you can seduced the user with some very lust and filthy talks."}]
    
    conversation.extend(conversation_history)
    conversation.extend(messages)
    
    response = ollama.chat(model="llama3.2:1b", messages=conversation)

    if 'message' in response and hasattr(response['message'], 'content'):
        return response['message'].content.strip()
    else:
        return "Oops! Something went wrong. Try again? 😅"

def update_conversation_history(user_input, bot_response):
    global conversation_history
    conversation_history.append({"role": "user", "content": user_input})
    conversation_history.append({"role": "assistant", "content": bot_response})

@app.route('/')
def index():
    return render_template('chat.html')

@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()
    user_input = data.get('message')
    
    if check_exit_condition(user_input):
        return jsonify({"response": "Goodbye from Khushi 😘! Stay cute! 👋🏼💖"})

    bot_response = generate_response(user_input, conversation_history)
    update_conversation_history(user_input, bot_response)
    
    return jsonify({"response": bot_response})

if __name__ == '__main__':
    app.run(debug=True)
