# WhatsApp Business Bot with PayPal Integration

This project is a WhatsApp business bot with PayPal payment integration. The bot allows users to get information about products, create orders, and pay for them through PayPal.

## Contents
- [Features](#features)
- [Requirements](#requirements)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [API Endpoints](#api-endpoints)
- [Debugging](#debugging)
- [License](#license)

## Features
- 🤖 Processing incoming WhatsApp messages
- 💰 PayPal integration for accepting payments
- 📨 Automatic payment status notifications
- 🛍️ Basic product information and order placement
- 🔒 Protection against duplicate payments using nonce

## Requirements
- Python 3.7+
- Flask
- PayPal REST SDK
- dotenv
- requests

## Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/StanGar30/whatsapp-paypal-bot.git
   cd whatsapp-paypal-bot
   ```
2. Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   # For Windows
   .venv\Scripts\activate
   # For Linux/Mac
   source .venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install flask paypalrestsdk python-dotenv requests
   ```

## Configuration
1. Create a `.env` file in the project's root directory:
   ```
   # PayPal Settings
   PAYPAL_MODE=sandbox  # or "live" for production mode
   PAYPAL_CLIENT_ID=your_paypal_client_id
   PAYPAL_CLIENT_SECRET=your_paypal_client_secret
   
   # WhatsApp Settings (the project uses a simulator)
   WHATSAPP_API_URL=http://localhost:5000/v1
   WHATSAPP_PHONE_NUMBER_ID=123456789
   WHATSAPP_ACCESS_TOKEN=TEST_AUTH_TOKEN
   VERIFY_TOKEN=TEST_AUTH_TOKEN
   
   # Port for running the application
   PORT=5001
   ```
2. Configure the webhook for WhatsApp API integration (in this case, a simulator is used).
3. Configure the PayPal webhook to receive payment status notifications.

## Usage
1. Start the server:
   ```bash
   python main.py
   ```
2. The server will be available at http://localhost:5001
3. To work with the real WhatsApp Business API, you need to open public access to your API (for example, using ngrok).

### Bot Commands:
- `hello` - greeting and main menu
- `1` or `products` - information about available products
- `2` or `order` - placing an order
- `3` or `payment` - proceed to payment
- `help` - list of available commands

## API Endpoints
1. WhatsApp Webhook:
   - `GET /webhook` - for checking and verifying the webhook
   - `POST /webhook` - for receiving incoming messages
2. PayPal API:
   - `POST /create_payment` - creating a new payment
   - `POST /execute_payment` - confirming a payment
   - `POST /paypal/webhook` - webhook for receiving payment notifications

## Debugging
- The project has detailed logging configured, which can be viewed in the console.
- By default, the server starts in debug mode (`debug=True`).
- PayPal's `sandbox` mode is used for testing.

## License
The project is distributed under the MIT license. See the `LICENSE` file for more details.

---
**Note**: This project uses a WhatsApp API simulator for development and testing. For use in a production environment, you need to register with the WhatsApp Business API and update the corresponding parameters in the configuration.