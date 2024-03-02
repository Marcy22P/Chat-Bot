from flask import Flask, request
import requests
import openai
import os
import json

# Imposta le chiavi API come variabili d'ambiente per motivi di sicurezza
openai_api_key = os.getenv('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')# Da cambiare in variabili d'ambiente
gohighlevel_api_key = os.getenv('eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJsb2NhdGlvbl9pZCI6InFLVWZKMHRyd2FOUjdRNHZqRlVNIiwiY29tcGFueV9pZCI6ImFXalZmdUxBYXhJOU03ZVdpYXE4IiwidmVyc2lvbiI6MSwiaWF0IjoxNjkxMTM3MTc2Mjg2LCJzdWIiOiJpV2kwR24zUURLcm5pY05xV1FpUSJ9.umkXvuK0mU-ewv9iR-50RMYFZ3l9biyUWWDjuqNqpYM')  # Da cambiare in variabili d'ambiente
assistant_id = os.getenv('asst_d3oUbNFuuoKzsuggRHde6g3N')  # Da cambiare in variabili d'ambiente

app = Flask(__name__)

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    contact_id = data.get('contactId')  # Assumendo che 'contactId' sia passato nel webhook
    customer_message = data.get('SMS')  # Assumendo che 'SMS' sia la chiave del messaggio inviato
    response = talk_to_openai(customer_message)
    send_response_to_gohighlevel(contact_id, response)
    return "OK", 200

def talk_to_openai(message):
    openai.api_key = openai_api_key
    response = openai.Completion.create(
      model="gpt-4-1106-preview",  # Sostituisci con il modello dell'assistant 
      prompt=message,
      max_tokens=150,
      assistant_id="asst_d3oUbNFuuoKzsuggRHde6g3N" # Usa l'ID del tuo assistant qui
    )
    return response.choices[0].text.strip()

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
