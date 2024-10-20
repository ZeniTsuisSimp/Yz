from flask import Flask, render_template, request, jsonify, session
from google.cloud import dialogflow_v2 as dialogflow
import os
# from dotenv import loadenv
import uuid
import secrets
import google.generativeai as genai

api_key = "AIzaSyCC8w3fxJw3txacXivVYoYNlDbGmupkL44"

genai.configure(api_key=api_key)

# Create the model
generation_config = {
  "temperature": 1,
  "top_p": 0.95,
  "top_k": 64,
  "max_output_tokens": 8192,
  "response_mime_type": "text/plain",
}

history = []

app = Flask(__name__, template_folder='template', static_folder='static')
app.secret_key = secrets.token_hex(16)
@app.route("/")
def index():
    if 'conversation' not in session:
        session['conversation'] = []
        session['session_id'] = str(uuid.uuid4())
    return render_template('chat.html')

@app.route("/get", methods=["POST"])
def chat():
    msg = request.form["msg"]
    session['conversation'].append({'role': 'user', 'content': msg})
    response = get_chat_response(msg)
    session['conversation'].append({'role': 'assistant', 'content': response})
    return jsonify({"response": response})


# Initialize conversation history globally (empty at the start)
history = []

# Set up generation configuration
generation_config = genai.GenerationConfig(
    max_tokens=150,  # Define how many tokens the response can have
    temperature=0.7,  # Controls randomness
    top_p=0.9,  # Controls nucleus sampling
)

def get_chat_response(text_input):
    try:
        # Set up the Generative AI model
        model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            generation_config=generation_config,
        )
        
        # Start a chat session with the model, including the conversation history
        chat_session = model.start_chat(
            history=history
        )

        # Send the user's message to the model and get the response
        response = chat_session.send_message(text_input)

        # Update conversation history (keeping a maximum of 5 turns)
        if len(history) <= 5:
            history.append({'role': 'user', 'content': text_input})
            history.append({'role': 'assistant', 'content': response.text})
        else:
            history.pop(0)  # Remove oldest turn if history exceeds 5
            history.append({'role': 'user', 'content': text_input})
            history.append({'role': 'assistant', 'content': response.text})

        # Return the model's response text
        return response.text
    except Exception as e:
        return str(e)


@app.route("/clear", methods=["POST"])
def clear_conversation():
    session.pop('conversation', None)
    session.pop('session_id', None)
    return jsonify({"response": "Conversation cleared!"})

if __name__ == '__main__':
    app.run(debug=True)
