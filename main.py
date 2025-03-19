import os
from flask import Flask, request, jsonify
from dotenv import load_dotenv
import requests
import json
import logging
import re
from paypal_connect import create_payment, execute_payment
from hashlib import sha256
import hmac
import base64

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', filename='app.log')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# WhatsApp API settings
WHATSAPP_API_URL = "http://api.whatsapp.com"    # WhatsApp API URL
WHATSAPP_PHONE_NUMBER_ID = "123456789"          # ID phone number
WHATSAPP_ACCESS_TOKEN = "TEST_AUTH_TOKEN"       # Test access token
VERIFY_TOKEN = "TEST_AUTH_TOKEN"                # Test verify token
MAX_MESSAGE_LENGTH = 2000                       # Maximum message length

app = Flask(__name__)


# Function to send a WhatsApp message
def send_whatsapp_message(to, message):
    url = f"{WHATSAPP_API_URL}/messages"                            # WhatsApp API URL
    headers = {                                                     # Headers for the request
        "Content-Type": "application/json",                         # Content type
        "Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}"          # Authorization token
    }
    payload = {                                                     # Payload for the request
        "to": to,                                                   # Recipient phone number
        "text": message,                                            # Message text
        "type": "text"                                              # Message type
    }

    try:
        response = requests.post(url, headers=headers, json=payload)    # Send the message
        response.raise_for_status()                                     # Check for errors
        logger.info(f"Message sent successfully: {response.json()}")    # Log the response

        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Error sending message: {e}")

        return None


# Webhook for receiving messages from WhatsApp
@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json                                                                                             # Get the request data
    logger.info(f"Received webhook data: {data}")

    try:
        if data.get('object') and data.get('entry') and data['entry'][0].get('changes'):                            # Check for the required fields
            change = data['entry'][0]['changes'][0]                                                                 # Get the change data
            if change.get('value') and change['value'].get('messages') and len(change['value']['messages']) > 0:    # Check for the message data

                message = change['value']['messages'][0]                                                            # Get the message data

                phone_number = message['from']                                                                      # Get the sender's phone number
                message_body = message.get('text', {}).get('body', '')                                              # Get the message body
                message_id = message['id']                                                                          # Get the message ID

                response_message = process_message(message_body, phone_number)                                      # Process the message

                send_whatsapp_message(phone_number, response_message)                                               # Send the response message

        return jsonify({"status": "success"}), 200
    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

# PayPal webhook for receiving payment notifications
@app.route('/paypal/webhook', methods=['POST'])
def paypal_webhook():
    data = request.json                                                                 # Get the request data
    logger.info(f"Received PayPal webhook data: {data}")
    signature = request.headers.get('X-PayPal-Transmission-Signature')                  # Get the signature
    secret_key = "your_webhook_secret"

    try:
        if not signature:                                                               # Check for the signature
            return jsonify({"status": "error", "message": "Missing signature"}), 400

        payload = json.dumps(data).encode()                                             # Encode the payload
        expected_signature = base64.b64encode(                                          # Generate the expected signature
            hmac.new(secret_key.encode(), payload, sha256).digest()
        ).decode()

        if signature != expected_signature:                                             # Check the signature
            return jsonify({"status": "error", "message": "Invalid signature"}), 401

        if not data or 'event_type' not in data or 'resource' not in data:              # Check for the required fields
            return jsonify({"status": "error", "message": "Invalid webhook data"}), 400

        if data.get('event_type') == 'PAYMENT.SALE.COMPLETED':                                  # Check for the payment completed event
            phone_number = data['resource'].get('custom')                                       # Get the phone number
            send_whatsapp_message(phone_number, "Your payment has been completed.")    # Send a message
        elif data.get('event_type') == 'PAYMENT.SALE.REFUNDED':                                 # Check for the payment refunded event
            phone_number = data['resource'].get('custom')                                       # Get the phone number
            send_whatsapp_message(phone_number, "Your payment has been refunded.")      # Send a message
        return jsonify({"status": "success"}), 200
    except Exception as e:
        logger.error(f"Error processing PayPal webhook: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

# PayPal payment creation route
@app.route('/create_payment', methods=['POST'])
def create_payment_route():
    data = request.json                                                                                         # Get the request data
    logger.info(f"Received payment creation request: {data}")

    try:
        if not data or 'payment' not in data or not isinstance(data['payment'], dict):                          # Check for the required fields
            return jsonify({"status": "error", "message": "Invalid payment data"}), 400

        payment_amount = data['payment'].get('amount', 0)                                                       # Get the payment amount
        currency = data['payment'].get('currency', 'USD')                                                       # Get the currency
        return_url = data['payment'].get('return_url', 'http://return.url')                                     # Get the return URL
        cancel_url = data['payment'].get('cancel_url', 'http://cancel.url')                                     # Get the cancel URL

        approval_url, payment_id = create_payment(payment_amount, currency, return_url, cancel_url)             # Create the payment
        if approval_url:                                                                                        # Check if the payment was created successfully
            return jsonify({"status": "success", "approval_url": approval_url, "payment_id": payment_id}), 200
        else:
            return jsonify({"status": "error", "message": "Payment creation failed"}), 500
    except Exception as e:
        logger.error(f"Error creating payment: {e}")
        return jsonify({"status": "error", "message": str(e)}), 400

# PayPal payment execution route
@app.route('/execute_payment', methods=['POST'])
def execute_payment_route():
    data = request.json                                                                             # Get the request data
    logger.info(f"Received payment execution request: {data}")

    try:
        payment_id = data.get('payment_id')                                                         # Get the payment ID
        payer_id = data.get('payer_id')                                                             # Get the payer ID
        nonce = data.get('nonce')                                                                   # Get the nonce

        if not payment_id or not payer_id or not nonce:                                             # Check for the required fields
            return jsonify({"status": "error", "message": "Invalid payment data"}), 400

        if execute_payment(payment_id, payer_id, nonce):                                            # Execute the payment
            return jsonify({"status": "success", "message": "Payment executed successfully"}), 200
        else:
            return jsonify({"status": "error", "message": "Payment execution failed"}), 500
    except Exception as e:
        logger.error(f"Error executing payment: {e}")
        return jsonify({"status": "error", "message": str(e)}), 400

# Verify webhook route
@app.route('/webhook', methods=['GET'])
def verify_webhook():
    mode = request.args.get('hub.mode')                                                 # Get the hub mode - required for verification
    token = request.args.get('hub.verify_token')                                        # Get the verify token - required for verification
    challenge = request.args.get('hub.challenge')                                       # Get the challenge - required for verification

    if mode and token and mode == 'subscribe' and token == VERIFY_TOKEN:                # Check for the required fields, mode, and token
        logger.info(f"Webhook verified with challenge: {challenge}")
        return challenge, 200
    else:
        logger.warning("Webhook verification failed")
        return jsonify({"status": "error", "message": "Verification failed"}), 403


# Function to process incoming messages
def process_message(message_text, sender):
    """
    Incoming message processing logic.
    """
    message_text = message_text.lower().strip()

    # Check for empty message
    if not message_text:
        return "I'm sorry, I didn't understand that. Please try again."

    # Check for message length
    if message_text.lower() in ['hi', 'hello', 'hey']:
        return "Hello! How can I help you today?"

    # Basic message processing logic
    if len(message_text) > MAX_MESSAGE_LENGTH:
        return "Message is too long. Please keep it under 2000 characters."

    # Check for invalid characters
    if re.fullmatch(r"[^a-zA-Zа-яА-Я0-9\s]+", message_text):
        return "I`m sorry, I can`t process special characters. Please try again."

    # Check for specific commands
    if message_text in ['hi', 'hello', 'hey']:
        return "Hello! How can I help you today?"

    # Check for specific commands
    elif message_text in ['1', 'products', 'products', 'products info']:
        return "We have the following products available:\n1. Product 1\n2. Product 2\n3. Product 3"

    # Check for specific commands
    elif message_text.startswith(('order', '2')):
        return "Your order has been placed successfully. You will receive a confirmation shortly."

    # Check for specific commands
    elif message_text in ['3', 'payment', 'payment', 'payment info']:
        return "Payment options:\n1. Credit Card\n2. PayPal\n3. Bitcoin"

    # Check for specific commands
    elif message_text in ['help', 'commands', 'info']:
        return "Commands:\n1. Products - Get information about available products\n2. Order - Place an order\n3. Payment - Get payment information"

    else:
        return "I'm sorry, I didn't understand that. Please try again."


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    app.run(host='0.0.0.0', port=port, debug=True)