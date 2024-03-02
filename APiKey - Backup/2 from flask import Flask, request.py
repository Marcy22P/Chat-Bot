from flask import Flask, request
import requests
import openai
import os

# Imposta le chiavi API come variabili d'ambiente per motivi di sicurezza
openai_api_key = os.getenv('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')
gohighlevel_api_key = os.getenv('eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJsb2NhdGlvbl9pZCI6InFLVWZKMHRyd2FOUjdRNHZqRlVNIiwiY29tcGFueV9pZCI6ImFXalZmdUxBYXhJOU03ZVdpYXE4IiwidmVyc2lvbiI6MSwiaWF0IjoxNjkxMTM3MTc2Mjg2LCJzdWIiOiJpV2kwR24zUURLcm5pY05xV1FpUSJ9.umkXvuK0mU-ewv9iR-50RMYFZ3l9biyUWWDjuqNqpYM')
assistant_id = os.getenv('asst_d3oUbNFuuoKzsuggRHde6g3N')  # ID del tuo assistant

app = Flask(__name__)

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    customer_message = data.get('SMS')  # Assumiendo che 'SMS' sia la chiave del messaggio inviato
    response = talk_to_openai(customer_message)
    send_response_to_gohighlevel(response)
    return "OK", 200

def talk_to_openai(message):
    openai.api_key = openai_api_key
    response = openai.ChatCompletion.create(
      model="gpt-4-1106-preview",  # Sostituisci con il modello dell'assistant se necessario
      messages=[
          {"role": "system", "content": "Your system message here"},
          {"role": "user", "content": message}
      ],
      assistant_id=asst_d3oUbNFuuoKzsuggRHde6g3N  # Usa l'ID del tuo assistant qui
    )
    return response['choices'][0]['message']['content']

def send_response_to_gohighlevel(response):
    url = "https://services.leadconnectorhq.com/hooks/qKUfJ0trwaNR7Q4vjFUM/webhook-trigger/f76ee411-355b-49af-ad5f-bccda80d45b5"  # Endpoint specifico di GoHighLevel
    headers = {
        'Authorization': f'Bearer {gohighlevel_api_key}',
        'Content-Type': 'application/json'
    }
    data = {'response': response}  # Adatta questa struttura in base a come GoHighLevel si aspetta la risposta
    response = requests.post(url, json=data, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Errore: {response.status_code}")
        return None

if __name__ == '__main__':
    app.run(debug=True)
