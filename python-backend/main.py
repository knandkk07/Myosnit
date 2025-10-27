from flask import Flask, request, jsonify
from flask_cors import CORS
from pyrogram import Client
import asyncio
import re
import os

app = Flask(__name__)
CORS(app)

# Telegram Configuration
API_ID = int(os.getenv('API_ID', 'YOUR_API_ID'))  # Replace from environment
API_HASH = os.getenv('API_HASH', 'YOUR_API_HASH')  # Replace from environment
PHONE_NUMBER = os.getenv('PHONE_NUMBER', '+916206785398')
BOT_USERNAME = '@ZaverinBot'

# Initialize Pyrogram client
client = Client(
    "leakosint_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    phone_number=PHONE_NUMBER
)

def parse_bot_response(text):
    """Parse the bot response and extract relevant information"""
    results = []
    
    # Split by records (each record starts with 📞Telephone or similar)
    records = text.split('📞Telephone:')
    
    for record in records[1:]:  # Skip first empty split
        data = {}
        
        # Extract phone numbers
        phones = re.findall(r'(\d{12,13})', record)
        if phones:
            data['phones'] = ['+' + p if not p.startswith('+') else p for p in phones]
        
        # Extract address
        address_match = re.search(r'🏘️Adres:\s*([^\n]+)', record)
        if address_match:
            data['address'] = address_match.group(1).strip()
        
        # Extract full name
        name_match = re.search(r'👤Full name:\s*([^\n]+)', record)
        if name_match:
            data['fullName'] = name_match.group(1).strip()
        
        # Extract father's name
        father_match = re.search(r'👨The name of the father:\s*([^\n]+)', record)
        if father_match:
            data['fatherName'] = father_match.group(1).strip()
        
        # Extract region
        region_match = re.search(r'🗺️ Region:\s*([^\n]+)', record)
        if region_match:
            data['region'] = region_match.group(1).strip()
        
        # Extract document number
        doc_match = re.search(r'🃏Document number:\s*([^\n]+)', record)
        if doc_match:
            data['documentNumber'] = doc_match.group(1).strip()
        
        if data:
            results.append(data)
    
    return results

async def search_telegram_bot(phone_number):
    """Send message to bot and get response"""
    try:
        await client.start()
        
        # Send message to bot
        await client.send_message(BOT_USERNAME, phone_number)
        
        # Wait for response (adjust timeout as needed)
        await asyncio.sleep(5)
        
        # Get last message from bot
        async for message in client.get_chat_history(BOT_USERNAME, limit=1):
            if message.text:
                return message.text
        
        return None
        
    except Exception as e:
        print(f"Error in Telegram communication: {e}")
        return None
    finally:
        await client.stop()

@app.route('/search', methods=['POST', 'OPTIONS'])
def search():
    # Handle CORS preflight
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        data = request.get_json()
        query = data.get('query', '').strip()
        
        if not query:
            return jsonify({'error': 'Phone number is required'}), 400
        
        # Validate phone format
        if not re.match(r'^\+91\d{10}$', query):
            return jsonify({'error': 'Invalid phone number format'}), 400
        
        # Get response from Telegram bot
        bot_response = asyncio.run(search_telegram_bot(query))
        
        if not bot_response:
            return jsonify({'error': 'No response from bot'}), 500
        
        # Parse the response
        parsed_data = parse_bot_response(bot_response)
        
        if not parsed_data:
            return jsonify({
                'message': 'No results found',
                'data': []
            })
        
        return jsonify({
            'success': True,
            'count': len(parsed_data),
            'data': parsed_data,
            'raw_response': bot_response  # For debugging
        })
        
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy', 'service': 'Leakosint Search API'})

@app.route('/', methods=['GET'])
def home():
    return jsonify({
        'service': 'Leakosint Search API',
        'version': '1.0',
        'endpoints': {
            '/search': 'POST - Search for phone number',
            '/health': 'GET - Health check'
        }
    })

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
