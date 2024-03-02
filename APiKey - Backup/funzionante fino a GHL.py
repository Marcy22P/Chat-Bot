from flask import Flask, request, jsonify
import requests
import os
from openai import OpenAI

# Inizializza il client OpenAI per il tuo assistente
assistant_api_key = os.getenv('ASSISTANT_API_KEY')  # Sostituisci con la tua API Key dell'assistente
assistant_client = OpenAI(api_key=assistant_api_key)

# Inizializza il client OpenAI per il completions (GPT-4)
gohighlevel_api_key = os.getenv('GOHIGHLEVEL_API_KEY')
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

app = Flask(__name__)

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    app.logger.info("Ricevuta una richiesta JSON: %s", data)
    
    if "message" in data:
        message_value = data["message"]
        contact_id = data.get('contactId')
        response = talk_to_openai(message_value)
        print(response)
        app.logger.info("Risposta da OpenAI: %s", response)
        
        if response:
            if send_response_to_gohighlevel(contact_id, response):
                return jsonify({"status": "OK"})
            else:
                return jsonify({"status": "Errore nell'invio a GoHighLevel"}), 500
        else:
            return jsonify({"status": "Errore nell'interazione con OpenAI"}), 500
    else:
        return jsonify({"status": "Nessun messaggio trovato"}), 400

@app.route('/assistant', methods=['POST'])
def assistant():
    data = request.json
    app.logger.info("Ricevuta una richiesta JSON per l'assistente: %s", data)
    
    if "message" in data:
        message_value = data["message"]
        
        try:
            response = assistant_client.chat.completions.create(
                model="gpt-4-1106-preview",  # Sostituisci con il modello del tuo assistente
                messages=[
                    {"role": "system", "content": "Il tuo messaggio di sistema qui"},
                    {"role": "user", "content": message_value}
                ]
            )
            
            assistant_response = response.choices[0].message.content
            
            return jsonify({"assistant_response": assistant_response})
        
        except Exception as e:
            app.logger.error("Si è verificato un errore con l'assistente: %s", str(e))
            return jsonify({"status": "Errore nell'interazione con l'assistente"}), 500
    else:
        return jsonify({"status": "Nessun messaggio trovato per l'assistente"}), 400

def talk_to_openai(message):
    try:
        response = client.chat.completions.create(
            model="gpt-4-1106-preview",
            messages=[
                {"role": "system", "content": "Il tuo messaggio di sistema qui"},
                {"role": "user", "content": message}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        app.logger.error("Si è verificato un errore con OpenAI: %s", str(e))
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
    response = requests.post(url, headers=headers, json=payload)
    
    if response.status_code == 200:
        return True
    else:
        app.logger.error("Errore nell'invio a GoHighLevel: %s", response.status_code)
        return False

if __name__ == '__main__':
    app.run(debug=True)
