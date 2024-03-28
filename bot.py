from openai import OpenAI
import requests
import telebot
import os
import json

with open('config.json') as config_file:
    config_data = json.load(config_file)

BOT_TOKEN = config_data['token']
bot = telebot.TeleBot(BOT_TOKEN)

API_KEY = os.environ["OPENAI_API_KEY"]
CATAPI_KEY = os.environ["CATAPI_KEY"]

client = OpenAI(
    api_key = API_KEY
)

chat_log = []

def get_cat_image(): # call CatAPI and request for the url
    response = requests.get("https://api.thecatapi.com/v1/images/search", headers={"x-api-key": CATAPI_KEY})
    if response.status_code == 200:
        return response.json()[0]['url']
    else:
        return None
    
def get_cat_breed_image(breed):
    url = "https://api.thecatapi.com/v1/breeds"
    response = requests.get(url)
    breed_id = None
    if response.status_code == 200:
        breeds = response.json()
        for line in breeds:
            if breed.lower() == line['name'].lower():
                breed_id = line['id']
    if breed_id is None:
        return "The breed you looking for does not exist :("
    response = requests.get(f"https://api.thecatapi.com/v1/images/search?breed_ids={breed_id}", headers={"x-api-key": CATAPI_KEY})
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

# Define a command handler
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "Welcome to Cat ChatBot! Type /info to get more information. I will provide any amount of cat pictures you desire")

@bot.message_handler(commands=['info'])
def send_info(message):
    bot.reply_to(message, "Just simply ask me for cat pictures and their breeds and I will send it to you (:")

@bot.message_handler(commands=['clear'])
def clear_message(message):
    global chat_log
    chat_log.clear()
    bot.reply_to(message, "Chat logs have been cleared")

# Define a message handler
@bot.message_handler(func=lambda message: True)
def echo_all(message):
    global chat_log
    print(message.from_user.id)
    tools = [
        {
            "type": "function",
            "function" : {
                "name": "get_cat_image",
                "description": "get image of cat",
                "parameters": {
                }
            }
        },
        {
            "type": "function",
            "function" : {
                "name": "get_cat_breed_image",
                "description": "get image of cat base on the breed input",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "breed": {
                            "type": "string",
                            "description": "The breed of the cat eg. Siamese, Bengal",
                        },
                    },
                    "required": ["breed"],
                }
            }
        }
    ]
    chat_log.append({"role":"user", "content": message.text})
    
    response = client.chat.completions.create(
        model="gpt-4-turbo-preview",
        tools = tools,
        tool_choice="auto",
        messages=chat_log
    )
    assistant_response = response.choices[0].message
    tool_calls = assistant_response.tool_calls
    if tool_calls:
        available_functions = {
            "get_cat_image": get_cat_image,
            "get_cat_breed_image": get_cat_breed_image,
        }
        chat_log.append({"role": "assistant", "content": "Here are some cat pictures:"})
        bot.send_message(message.chat.id, "Here are some cat pictures:")
        for tool_call in tool_calls:
            function_name = tool_call.function.name
            function_to_call = available_functions[function_name]
            function_args = json.loads(tool_call.function.arguments)
            if function_to_call:
                if function_args:
                    function_response = function_to_call(
                        breed = function_args.get("breed")
                    )
                else:
                    function_response = function_to_call()
                chat_log.append(
                    {
                        "role": "assistant",
                        "content": function_response,
                    }
                )
                bot.reply_to(message, function_response)
                if function_response == "The breed you looking for does not exist :(":
                    break
            else:
                chat_log.append(
                    {
                        "role": "assistant",
                        "content": "function not available",
                    }
                )
                bot.reply_to(message, "function not available")
    else:
        if not assistant_response.tool_calls:
            chat_log.append({"role": "assistant", "content": assistant_response.content})
            bot.send_message(message.chat.id, assistant_response.content)
    print(chat_log)  
    '''
    chat_log.append({"role": "user", "content": message.text})
    response = client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=chat_log
        )
    assistant_response = response.choices[0].message.content
    chat_log.append({"role": "user", "content": assistant_response})
    bot.reply_to(message, assistant_response)
    '''

# Start the bot
bot.polling()