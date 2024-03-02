from flask import Flask, request
import requests
import os
import json
from openai import OpenAI

# Inizializza il client OpenAI
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

gohighlevel_api_key = os.getenv('GOHIGHLEVEL_API_KEY')

app = Flask(__name__)

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    print(type (data))
    message_value = data["message"]
    
    contact_id = data.get('contactId')
    customer_message = data.get('message')
    response = talk_to_openai(message_value)
    send_response_to_gohighlevel(contact_id, response)

    return "OK", 200


def talk_to_openai(message):
    try:
        # Adesso utilizziamo il metodo 'create' dell'oggetto 'chat.completions' invece di 'ChatCompletion.create'
        response = client.chat.completions.create(
            model="gpt-4-1106-preview",
            messages=[
                {"role": "system", "content": "Your system message here"},
                {"role": "user", "content": message}
            ]
        )

        # Assumendo che la struttura di risposta sia una lista di messaggi, accediamo al primo elemento.
        return response["choices"][0]["message"]["content"]
    except Exception as e:
        # Aggiungi qui la logica per gestire l'eccezione e fare il debug.
        print(f"Si è verificato un errore: {e}")
        return None


def send_response_to_gohighlevel(contact_id, message):
    url = "https://services.leadconnectorhq.com/conversations/messages"
    headers = {
        'Accept': 'application/json',
        'Authorization': f'Bearer {gohighlevel_api_key}',
        'Content-Type': 'application/json',
        'Version': '2021-04-15'
    }
    payload = {
        "type": "SMS",
        "contactId": contact_id,
        "message": message
    }
    response = requests.post(url, headers=headers, data=json.dumps(payload))
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Errore: {response.status_code}")
        return None

if __name__ == '__main__':
    app.run(debug=True)
