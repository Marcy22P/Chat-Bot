from flask import Flask, request, jsonify
import logging
import sys
import requests
import os
from openai import OpenAI

# Inizializza il client OpenAI per il tuo assistente
assistant_api_key = os.getenv('ASSISTANT_API_KEY')  # Sostituisci con la tua API Key dell'assistente
assistant_client = OpenAI(api_key=assistant_api_key)

# Inizializza il client OpenAI per il completions (GPT-4)
gohighlevel_api_key = os.getenv('GOHIGHLEVEL_API_KEY')
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# Dizionario per tenere traccia delle cronologie delle chat per ogni ID utente
chat_histories = {}

app = Flask(__name__)

@app.route('/webhook', methods=['GET','POST'])
def webhook():
    data = request.json
    app.logger.info("Ricevuta una richiesta JSON: %s", data)
    
    if "message" in data:
        message_value = data["message"]
        contact_id = data["contact_id"]
        phone = data["phone"]
        response = talk_to_openai(message_value, contact_id)
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
                model="gpt-4-1106-preview", 
                messages=[
                    {"role": "system", "content": "Privacy, no role"},
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


def talk_to_openai(message, contact_id):
    # Se l'utente non esiste nel dizionario, inizializza una nuova cronologia della chat
    if contact_id not in chat_histories:
        chat_histories[contact_id] = [{"role": "assistant", "content": "Privacy no role"
    # Aggiungi il messaggio dell'utente alla cronologia della chat
    chat_histories[contact_id].append({"role": "user", "content": message})
    try:
        response = client.chat.completions.create(
            model="gpt-4-1106-preview",
            messages=chat_histories[contact_id]
        )
        chat_histories[contact_id].append({"role": "assistant", "content": response.choices[0].message.content}) 
        return response.choices[0].message.content
    except Exception as e:
        app.logger.error("Si è verificato un errore con OpenAI: %s", str(e))
        return None

def send_response_to_gohighlevel(contact_id, message):
    webhook_url = "https://services.leadconnectorhq.com/hooks/qKUfJ0trwaNR7Q4vjFUM/webhook-trigger/a40ed9ac-dfa0-494f-b2da-91649dab6871"
    headers = {
        'Content-Type': 'application/json'
    }
    payload = {
        "contact_id": contact_id,  # chiave corretta come da aspettative di GoHighLevel
        "message": message
    }
    response = requests.post(webhook_url, headers=headers, json=payload)
    
    if response.status_code == 200:
        return True
    else:
        app.logger.error("Errore nell'invio a GoHighLevel: %s", response.status_code)
        return False


if __name__ == '__main__':
    app.run(debug=True)
