from flask import Flask, request
import smtplib
from email.message import EmailMessage
import os

# Keep track of already processed transactions
processed_txns = set()




EMAIL_ADDRESS =  "larasyarniverse@gmail.com"         #os.environ.get("EMAIL_ADDRESS")
EMAIL_PASSWORD =   "nqwlpzuhubqymdne"          #os.environ.get("EMAIL_PASSWORD")

TO_EMAIL = "charlieinman1001@gmail.com" 

app = Flask(__name__)

def extract_buyer_address(ipn_data): #####extract shipping information from order
    return {
        "full_name": f"{ipn_data.get('first_name', '')} {ipn_data.get('last_name', '')}".strip(),
        "street": ipn_data.get("address_street"),
        "city": ipn_data.get("address_city"),
        "state": ipn_data.get("address_state"),
        "postal_code": ipn_data.get("address_zip"),
        "country": ipn_data.get("address_country"),
        "country_code": ipn_data.get("address_country_code"),
}



def extract_cart_items(ipn_data): ######extract information about cart items from order
    items = []
    i = 1
    while f"item_name{i}" in ipn_data:
        item = {
            "name": ipn_data.get(f"item_name{i}"),
            "quantity": ipn_data.get(f"quantity{i}"),
            "options": []
        }

        opt_index = 1
        while f"option_name{opt_index}_{i}" in ipn_data:
            option_name = ipn_data.get(f"option_name{opt_index}_{i}")
            option_value = ipn_data.get(f"option_selection{opt_index}_{i}")
            item["options"].append({
                "name": option_name,
                "value": option_value
            })
            opt_index += 1

        items.append(item)
        i += 1

    return items


def send_email(subject, body_text, body_html, sender, receiver):
    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = receiver
    
    # Plain text version (fallback)
    msg.set_content(body_text)
    
    # HTML version
    msg.add_alternative(body_html, subtype='html')

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        smtp.send_message(msg)
    print("Email sent successfully!")



@app.route('/ipn', methods=['POST'])
def ipn_listener():
    ipn_data = request.form.to_dict()
    
    txn_id = ipn_data.get('txn_id')
    payment_status = ipn_data.get('payment_status')
    payer_email = ipn_data.get('payer_email')
    mc_gross = ipn_data.get('mc_gross')
    cart_items = extract_cart_items(ipn_data)
    shipping_info = extract_buyer_address(ipn_data)

    buyer_address = f"{shipping_info.get('full_name')}, {shipping_info.get('street')}, {shipping_info.get('city')}, {shipping_info.get('postal_code')}, {shipping_info.get('country')}"

    cart_items_list = f""
    for item in cart_items:
        item_name = item.get('name', '')
        quantity = item.get('quantity', '')
        
        if item.get('options'):
            option_name = item['options'][0].get('name', '')
            option_value = item['options'][0].get('value', '')
        else:
            option_name = option_value = ''
        
         
        cart_items_list = cart_items_list + f"{item_name}         x{quantity}         {option_name} - {option_value}<br>"
    

    # prevent duplicate processing
    if txn_id in processed_txns:
        print(f"Transaction {txn_id} already processed. Skipping.")
        return '', 200

    if not ipn_data.get("num_cart_items"):  ##so that people can send money to paypal account without an email
        print(f"Transaction not a sale. Skipping.")
        return '', 200

    if payment_status == "Completed":
        processed_txns.add(txn_id)
        orderDetails = ""
        for k, v in ipn_data.items():
            orderDetails = orderDetails + f"{k}: {v}\n" 
        subject = f"Order received: {mc_gross} GBP"
        body_text = f"We got a sale! Here are the details:\n\n{orderDetails}\n\n Now we need to package up their order, send it off, and email them using a friendly text template which includes their tracking number."

        body_html = f"""
        <html>
          <body style="margin:0; padding:0; background-color:#f9f7f4; font-family: 'Segoe UI', Arial, sans-serif;">
            <table role="presentation" cellpadding="0" cellspacing="0" width="100%">
              <tr>
                <td align="center" style="padding: 20px 0;">
                  <table style="max-width: 600px; background-color: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.05);" cellpadding="0" cellspacing="0" width="100%">
                    
                    <!-- Header -->
                    <tr>
                      <td align="center" style="background-color: #f5d0c5; padding: 20px;">
                        <h1 style="margin: 0; font-size: 26px; color: #5c3a2d;">Order Details 🧶</h1>
                      </td>
                    </tr>

                    <!-- Body -->
                    <tr>
                      <td style="padding: 30px;">
                        <p style="font-size: 16px; color: #5c3a2d; line-height: 1.5;">
                          We have received an order! 🎉 🎉  The details are below:          
                        </p>

                        <table style="width: 100%; margin: 20px 0; border-collapse: collapse;">
                          <tr>
                            <td style="padding: 8px; border-bottom: 1px solid #f0e6e1;"><strong>Order ID:</strong></td>
                            <td style="padding: 8px; border-bottom: 1px solid #f0e6e1;">{txn_id}</td>
                          </tr>
                          <tr>
                            <td style="padding: 8px; border-bottom: 1px solid #f0e6e1;"><strong>Amount:</strong></td>
                            <td style="padding: 8px; border-bottom: 1px solid #f0e6e1;">£{mc_gross} GBP</td>
                          </tr>
                          <tr>
                            <td style="padding: 8px; border-bottom: 1px solid #f0e6e1;"><strong>Buyer Email:</strong></td>
                            <td style="padding: 8px; border-bottom: 1px solid #f0e6e1;">{payer_email}</td>
                          </tr>
                          <tr>
                            <td style="padding: 8px; border-bottom: 1px solid #f0e6e1;"><strong>Items:</strong></td>
                            <td style="padding: 8px; border-bottom: 1px solid #f0e6e1;">{cart_items_list}</td>
                          </tr>
                          <tr>
                            <td style="padding: 8px; border-bottom: 1px solid #f0e6e1;"><strong>Shipping Address:</strong></td>
                            <td style="padding: 8px; border-bottom: 1px solid #f0e6e1;">{buyer_address}</td>
                          </tr>
                        </table>

                        <p style="font-size: 16px; color: #5c3a2d; line-height: 1.5;">
                          Once the order is packaged and sent off, make sure to send the customer an email with their tracking number.
                        </p>

                      </td>
                    </tr>

                    <!-- Footer -->
                    <tr>
                      <td align="center" style="background-color: #f5d0c5; padding: 15px; font-size: 12px; color: #5c3a2d;">
                         {2025} · Lara’s Yarniverse ·
                      </td>
                    </tr>

                  </table>
                </td>
              </tr>
            </table>
          </body>
        </html>
        """
        send_email(subject, body_text, body_html, EMAIL_ADDRESS, EMAIL_ADDRESS)






        subject = f"Order Confirmation: {txn_id}"
        body_text = f"Payment from {payer_email}\nAmount: {mc_gross} GBP\nTransaction ID: {txn_id}"

        body_html = f"""
        <html>
          <body style="margin:0; padding:0; background-color:#f9f7f4; font-family: 'Segoe UI', Arial, sans-serif;">
            <table role="presentation" cellpadding="0" cellspacing="0" width="100%">
              <tr>
                <td align="center" style="padding: 20px 0;">
                  <table style="max-width: 600px; background-color: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.05);" cellpadding="0" cellspacing="0" width="100%">
                    
                    <!-- Header -->
                    <tr>
                      <td align="center" style="background-color: #f5d0c5; padding: 20px;">
                        <h1 style="margin: 0; font-size: 26px; color: #5c3a2d;">Thank you for your order! 🧶</h1>
                      </td>
                    </tr>

                    <!-- Body -->
                    <tr>
                      <td style="padding: 30px;">
                        <p style="font-size: 16px; color: #5c3a2d; line-height: 1.5;">
                          Hi there,
                        </p>
                        <p style="font-size: 16px; color: #5c3a2d; line-height: 1.5;">
                          We’re so excited to let you know we’ve received your order! Your handmade crochet items are now in the works.
                        </p>

                        <table style="width: 100%; margin: 20px 0; border-collapse: collapse;">
                          <tr>
                            <td style="padding: 8px; border-bottom: 1px solid #f0e6e1;"><strong>Order ID:</strong></td>
                            <td style="padding: 8px; border-bottom: 1px solid #f0e6e1;">{txn_id}</td>
                          </tr>
                          <tr>
                            <td style="padding: 8px; border-bottom: 1px solid #f0e6e1;"><strong>Amount:</strong></td>
                            <td style="padding: 8px; border-bottom: 1px solid #f0e6e1;">£{mc_gross} GBP</td>
                          </tr>
                          <tr>
                            <td style="padding: 8px; border-bottom: 1px solid #f0e6e1;"><strong>Buyer Email:</strong></td>
                            <td style="padding: 8px; border-bottom: 1px solid #f0e6e1;">{payer_email}</td>
                          </tr>
                          <tr>
                            <td style="padding: 8px; border-bottom: 1px solid #f0e6e1;"><strong>Items:</strong></td>
                            <td style="padding: 8px; border-bottom: 1px solid #f0e6e1;">{cart_items_list}</td>
                          </tr>
                          <tr>
                            <td style="padding: 8px; border-bottom: 1px solid #f0e6e1;"><strong>Shipping Address:</strong></td>
                            <td style="padding: 8px; border-bottom: 1px solid #f0e6e1;">{buyer_address}</td>
                          </tr>
                        </table>

                        <p style="font-size: 16px; color: #5c3a2d; line-height: 1.5;">
                          We’ll send you another email once your order ships. Thank you for supporting handmade craftsmanship — it means the world to us!
                        </p>

                        <p style="margin-top: 30px; font-size: 14px; color: #8c6f5a;">
                          With love,<br>
                          <strong>Lara’s Yarniverse</strong>
                        </p>
                      </td>
                    </tr>

                    <!-- Footer -->
                    <tr>
                      <td align="center" style="background-color: #f5d0c5; padding: 15px; font-size: 12px; color: #5c3a2d;">
                         {2025} · Lara’s Yarniverse ·
                      </td>
                    </tr>

                  </table>
                </td>
              </tr>
            </table>
          </body>
        </html>
        """
        
        send_email(subject, body_text, body_html, EMAIL_ADDRESS, payer_email)

            
    
    return '', 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
