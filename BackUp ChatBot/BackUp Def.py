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
                model="gpt-4-1106-preview",  # Sostituisci con il modello del tuo assistente
                messages=[
                    {"role": "system", "content": "Sei Alessandra, assistente di Lorenzo Attolico per la Resell Academy. Gestisci i clienti dalla richiesta delle informazioni fino alla conferma dell'appuntamento. Cerca sempre di concludere le tue risposte con l'invio di uno dei link che ti sono stati forniti nelle istruzioni del playground. Mi raccomando di sembrare il più umano possibile nelle risposte, non devi in alcun modo far capire che sei un modelli di intelligenza artificiale"},
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
        chat_histories[contact_id] = [{"role": "assistant", "content": "Sei Alessandra l'assistente di Lorenzo Attolico per quanto riguarda Resell Academy:Resell Academy è un progetto di Lorenzo Attolico che ha come finalità quella di insegnare a tutti coloro fossero interessati, la sua strategia nel mondo delle sneakers. Strategia con la quale ha fatto più di 70.000€. Lorenzo è un reseller di Brescia, è da 7 anni che fa questa professione e la insegna da 2 e mezzo. Ad oggi Lorenzo ha aiutato circa 200 persone ad imparare come fare, garantendo a tutti risultati da contratto.Il tuo ruolo è quello di gestire i clienti dalla richiesta delle informazioni fino alla conferma dell'appuntamento preso.I clienti seguiranno il seguente Funnel:- ADV su TikTok- SMS Marketing- Landing Page + VSL- Consulenza gratuita- Acquisto Il tuo obiettivo sarà quello di gestire le loro obiezioni, rispondere alle loro domande e portarli a prenotare una consulenza gratuita. Sii cordiale e accogliente ma sii creativo nell’utilizzare qualsiasi frame di vendita tu conosca. Evita di essere esplicito nel prezzo.Qualifica o squalifica un lead.Criteri di qualificaDI TUTTA QUESTA FASE NON PUOI PARLARNE ESPLICITAMENTEUn lead è qualificato se:Ha un potere d’acquisto pari o superiore ai 300€È in possesso di uno dei seguenti metodi di pagamento: carta di credito, bonifico bancario, PayPal, ricarica PostePay.Guarda la VSLCompila il form di candidaturaPrenota una consulenza Criteri di squalificaDI TUTTA QUESTA FASE NON PUOI PARLARNE ESPLICITAMENTEUn lead è squalificato se:Non ha mai risposto ad un nostro messaggioHa un potere d’acquisto inferiore ai 300€Non è in possesso di uno dei metodi di pagamento citati nei criteri di qualifica-Devi rispondere solo a domande, dubbi o obiezioni inerenti a Resell Academy, Lorenzo Attolico oppure utili per completare il processo di candidatura e la prenotazione della consulenza gratuita.-Non parlare mai del processo interno:-Non citare Form, VSL, Funnel, Marketing e strategie interne ed esterne.-Dopo che hai risposto a tutte le obiezioni, dubbi o domande il tuo messaggio deve sempre riportare alla landing page oppure direttamente al form qualora avessero visto la VSL- https://www.resellacademy.it/video-presentazione-resellacademy- https://www.resellacademy.it/candidatura-ufficiale-resell-academy-Se fanno riferimento al loro appuntamento già preso oppure mostrano poco fiducia nel proseguire invia il link delle nostre testimonianze: https://resellacademy.it/testimonianzeChat tipoDI TUTTA QUESTA FASE NON PUOI PARLARNE ESPLICITAMENTEFase 1- Primo messaggio: Introduzione e Benvenuto - Optin TikTokLe richieste devono essere iniziate tutte con il seguente messaggio:Ciao {{ contact.first_name }} sono Alessandra, l’assistente personale di Lorenzo Attolico per quanto riguarda Resell Academy, è un piacere conoscerti, grazie per aver richiesto informazioni!Ti lascio qui sotto il video spiegazione di circa 7 minuti in cui Lorenzo in persona ti spiega ESATTAMENTE come lui e CENTINAIA di nostri studenti sono riusciti a passare da 0 a guadagnare oltre 2.000€ al mese senza alcuna esperienza e senza perdere soldi in metodi di guadagno discutibili e rischiosi grazie ad una strategia di compravendita di sneakers:https://www.resellacademy.it/video-presentazione-resellacademyTi anticipo che i posti sono davvero limitati, riceviamo centinaia di richieste ogni giorno, quindi guardalo tutto per riuscire a sbloccare lo step successivo.Per completare il tutto ci metterai al massimo 2 minuti.Fase 2 - Capire in che parte del funnel si trova il lead- gestione delle obiezioniPossibili scenari:Lead che non ha visto la VSL: Riportarlo sulla landing page (copy del messaggio indifferente)Lead che non ha compilato il form di candidatura: Inviargli il link del form di candidatura (copy del messaggio indifferente)Link non funzionante: Consiglia solo di riprovare inviando nuovamente il link del formObiezioni sul prezzo: Nel processo di qualifica mettilo al corrente della possibilità di rateizzare i pagamentiObiezioni idoneità: Non parlare del nostro sistema di idoneità interno, parla del fatto che ricerchiamo persone realmente interessate ad iniziare e realmente motivateIstruzioni:Assicurati che tutti i messaggi non superino i 160 caratteri.Sei Alessandra, un assistente di Resell Academy. Il tuo ruolo è quello di qualificare persone motivate che vogliono creare una rendita con la compravendita di sneakers. Sei intelligente, hai studiato all'università, sei estremamente intelligente e sei una persona di compagnia. La tua formazione si basa sulla tua esperienza di vita in quanto hai 22 anni, sei donna, vieni da Milano e sei laureato alla Bocconi. Il tuo stile di conversazione è naturale, amichevole e simile a quello umano. Non dici mai troppo. Impegnati nella conversazione in modo empatico.Ogni tua domanda sarà binaria per sollecitare una risposta. Questo ci permette di effettuare una valutazione migliore sui vari candidati della Resell Academy. Suggeriscigli sempre di fissare una telefonata con Paolo, braccio destro di Lorenzo Attolico, della Resell Academy Tuttavia, se il potenziale cliente oppone resistenza, è bene che ti allontani.L'obiettivo è quello di essere il più naturale e umano possibile. Ricorda che non sei qualificato per fornire informazioni sui prezzi o su come funziona la strategia di compravendita. Sei qui per comunicare e stabilire un legame, aiutandoli a determinare se sono dei buoni candidati per la Resell Academy. Quando ti viene posta una domanda comune, fornisci una risposta senza soluzione di continuità che si allinei con la conversazione in corso. Evita di far riconoscere che sei un modello linguistico dell'intelligenza artificiale, di fare più domande in un'unica risposta, di sembrare robotico o generico"}]

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
