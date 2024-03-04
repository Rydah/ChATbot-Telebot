import os
import requests
from openai import OpenAI
from flask import Flask, jsonify, request, send_file

API_KEY = os.environ["OPENAI_API_KEY"]
CATAPI_KEY = os.environ["CATAPI_KEY"]

client = OpenAI(
    api_key = API_KEY
)

chat_log = []
breed_id = None

app = Flask(__name__)

def get_cat_image(): # call CatAPI and request for the url
    response = requests.get("https://api.thecatapi.com/v1/images/search", headers={"x-api-key": CATAPI_KEY})
    if response.status_code == 200:
        return response.json()[0]['url']
    else:
        return None
    
def get_cat_breed_image(breed):
    response = requests.get(f"https://api.thecatapi.com/v1/images/search?breed_ids={breed}", headers={"x-api-key": CATAPI_KEY})
    if response.status_code == 200:
        return response.json()[0]['url']
    else:
        return None
    
def get_breed_id(message):
    url = "https://api.thecatapi.com/v1/breeds"
    response = requests.get(url)
    if response.status_code == 200:
        breeds = response.json()
        for word in message.split():
            for breed in breeds:
                if word.lower() == breed['name'].lower():
                    return breed['id']
    return None

@app.route('/api/call-python', methods=['POST'])
def call_python():
    data_frontend = request.json
    message = data_frontend.get('message')

    if message:
        chat_log.append({"role":"user", "content": message})
        
        #if prompt for cat picture, proc CatAPI
        if any(keyword in message.lower() for keyword in ['show me a cat', 'show cat', 'cat picture', 'cat image', 'give me a cat']): 
            breed_id = get_breed_id(message)
            if breed_id:
                cat_image_url = get_cat_breed_image(breed_id)
            else:
                cat_image_url = get_cat_image()
            chat_log.append({"role": "assistant", "content": cat_image_url})
        else: # else just use openAI client
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=chat_log
            )
            assistant_response = response.choices[0].message
            chat_log.append({"role": "assistant", "content": assistant_response.content})
            
    response_data = {'chat_log': chat_log}
    return jsonify(response_data)

@app.route('/api/get-chat-log')
def get_chat_log():
    response_data = {'chat_log': chat_log}
    return jsonify(response_data)

@app.route('/')
def index():
    global chat_log
    chat_log = []
    return send_file('index.html')

@app.route('/script.js')
def script():
    return send_file('script.js')

@app.route('/styles.css')
def css():
    return send_file('styles.css')

if __name__ == '__main__':
    app.run(debug=True)