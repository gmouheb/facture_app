from flask import Flask, render_template, request, make_response
from weasyprint import HTML, CSS
from weasyprint.text.fonts import FontConfiguration
import io
import json
from datetime import datetime

app = Flask(__name__)

# Add datetime.now function to templates
@app.context_processor
def inject_now():
    return {'now': datetime.now}


@app.route('/')
def index():
    """Display the invoice form"""
    return render_template('invoice_form.html')


@app.route('/generate_invoice', methods=['POST'])
def generate_invoice():
    """Process form data and generate invoice"""
    # Get form data
    items_json = request.form.get('items')
    items = json.loads(items_json)
    payment_method = request.form.get('payment_method', 'Virement bancaire')  # Default to bank transfer if not provided

    # Get shipping cost (can be null if left blank)
    shipping_cost_str = request.form.get('shipping_cost', '')
    shipping_cost = float(shipping_cost_str) if shipping_cost_str.strip() else 0

    # Get seller and client data
    seller_json = request.form.get('seller')
    client_json = request.form.get('client')

    seller = json.loads(seller_json) if seller_json else {
        'name': 'Nom de l\'entreprise',
        'address': '123 Rue du Commerce',
        'city': '75000 Paris, France',
        'phone': '01 23 45 67 89',
        'email': 'contact@entreprise.com'
    }

    client = json.loads(client_json) if client_json else {
        'name': 'Nom du client',
        'address': '456 Avenue du Client',
        'city': '75001 Paris, France',
        'phone': '01 98 76 54 32',
        'email': 'client@example.com'
    }

    # Calculate totals
    subtotal = sum(float(item['quantity']) * float(item['unit_price']) for item in items)
    tva = subtotal * 0.19  # 19% TVA on subtotal only
    total = subtotal + shipping_cost + tva

    # Render invoice template
    invoice_html = render_template(
        'invoice.html',
        items=items,
        subtotal=subtotal,
        shipping_cost=shipping_cost,
        tva=tva,
        total=total,
        payment_method=payment_method,
        seller=seller,
        client=client
    )

    return invoice_html


@app.route('/download_pdf', methods=['POST'])
def download_pdf():
    """Convert HTML invoice to PDF and offer for download"""
    invoice_html = request.form.get('invoice_html')

    # Replace relative URL with absolute path for the logo
    import os
    base_dir = os.path.abspath(os.path.dirname(__file__))
    logo_path = f"file://{os.path.join(base_dir, 'static', 'icons', 'img.png')}"
    invoice_html = invoice_html.replace('src="{{ url_for(\'static\', filename=\'icons/img.png\') }}"', f'src="{logo_path}"')

    # Configure fonts and CSS for A4 format
    font_config = FontConfiguration()
    css = CSS(string='''
        @page {
            size: A4;
            margin: 0;
        }
        @media print {
            body {
                margin: 0;
                padding: 0;
            }
        }
    ''', font_config=font_config)

    # Generate PDF from HTML with A4 format
    pdf = io.BytesIO()
    HTML(string=invoice_html, base_url=request.url_root).write_pdf(pdf, stylesheets=[css], font_config=font_config)
    pdf.seek(0)

    # Create response with PDF
    response = make_response(pdf.getvalue())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'attachment; filename=invoice.pdf'

    return response


if __name__ == '__main__':
    app.run(debug=True)
