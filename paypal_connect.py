import paypalrestsdk
import logging
from config import PAYPAL_MODE, PAYPAL_CLIENT_ID, PAYPAL_CLIENT_SECRET

# Logging configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', filename='paypal_connect.log')


# Configure PayPal SDK
paypalrestsdk.configure({
    "mode": PAYPAL_MODE,                                                    # Sandbox or live mode
    "client_id": PAYPAL_CLIENT_ID,                                          # PayPal client ID
    "client_secret": PAYPAL_CLIENT_SECRET                                   # PayPal client secret
})

# Create a payment
def create_payment(payment_amount, currency, return_url, cancel_url):
    """
    Creates a new payment and returns the approval URL for the payment.
    """
    payment = paypalrestsdk.Payment({   # Create a Payment object
        "intent": "sale",               # Sale intent - payment will be completed immediately
        "payer": {                      # Payer information - payment method
            "payment_method": "paypal"  # PayPal payment method - payer will be redirected to PayPal
        },
        "redirect_urls": {              # Redirect URLs after payment - success and cancel
            "return_url": return_url,   # URL to redirect to after successful payment
            "cancel_url": cancel_url    # URL to redirect to after payment cancellation
        },
        "transactions": [{              # Transaction details - payment amount and description
            "amount": {                 # Payment amount
                "total": f"{payment_amount:.2f}",   # Total amount
                "currency": currency                # Currency code - USD, EUR, etc.
            },
            "description": "Payment for services"   # Payment description
        }]
    })

    if payment.create():                        # Method for creating a payment
        logging.info("Payment created successfully")
        for link in payment.links:              # Get the approval URL from the payment links
            if link.method == "REDIRECT":       # Find the redirect link
                approval_url = str(link.href)   # Get the approval URL
                return approval_url, payment.id # Return the approval URL and payment ID
    else:
        logging.error("Error creating payment: %s", payment.error)
    return None, None

# Here SQL queries are used to store the nonce in the database, but you can use any other storage method.
used_nonces = set()

# Execute payment
def execute_payment(payment_id, payer_id, nonce):
    """
    Executes the payment with the given payment ID and payer ID.
    """
    if nonce in used_nonces:                                                                # Check if the nonce has already been used
        logging.error("ID has already been payment")
        return False

    used_nonces.add(nonce)                                                                  # Add the nonce to the used nonces set

    payment = paypalrestsdk.Payment.find(payment_id)                                        # Find the payment by ID
    if payment.execute({"payer_id": payer_id}):                                             # Execute the payment with the payer ID
        logging.info("Payment executed successfully")
        return True
    else:
        logging.error("Error executing payment: %s", payment.error)
        return False

# Check payment status
def check_payment_status(payment_id):
    """
    Returns the current status of the payment.
    """
    payment = paypalrestsdk.Payment.find(payment_id)                        # Find the payment by ID
    logging.info("Текущий статус платежа: %s", payment.state)
    return payment.state

# Refund payment
def refund_payment(sale_id, amount, currency):
    """
    Refunds the payment with the given sale ID, amount, and currency.
    """
    sale = paypalrestsdk.Sale.find(sale_id)                             # Find the sale by ID
    refund = sale.refund({                                              # Refund the sale with the given amount and currency
        "amount": {                                                     # Refund amount
            "total": f"{amount:.2f}",                                   # Total amount
            "currency": currency                                        # Currency code - USD, EUR, etc.
        }
    })
    if refund.success():                                                # Check if the refund was successful
        logging.info("Payment refunded successfully")
        return True
    else:
        logging.error("Error refunding payment: %s", refund.error)
    return False

if __name__ == "__main__":
    payment_amount = 10.00                                  # Payment amount
    currency = "USD"                                        # Currency code

    return_url = "https://yourdomain.com/payment/execute"  # Your return URL, where PayPal will redirect the user after payment
    cancel_url = "https://yourdomain.com/payment/cancel"   # Your cancel URL, where PayPal will redirect the user after payment cancellation

    # Create a payment
    approval_url, payment_id = create_payment(payment_amount, currency, return_url, cancel_url)
    if approval_url:
        print("Send the user to the following URL to approve the payment:")
        print(approval_url)
        print("ID of the created payment:", payment_id)
    else:
        print("Error creating payment")
