import os
import openai
import google.generativeai as genai
from flask import Flask, request, jsonify
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Configure API keys from environment variables
openai.api_key = os.environ.get("OPENAI_API_KEY")
genai.configure(api_key=os.environ.get("GOOGLE_API_KEY"))

@app.route('/api/generate', methods=['POST'])
def generate():
    data = request.get_json()
    model = data.get('model')
    prompt = data.get('prompt')

    if not model or not prompt:
        return jsonify({'error': 'Model and prompt are required'}), 400

    try:
        if model == 'chatgpt':
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}]
            )
            return jsonify({'response': response.choices[0].message.content})
        elif model == 'gemini':
            model = genai.GenerativeModel('gemini-pro')
            response = model.generate_content(prompt)
            return jsonify({'response': response.text})
        elif model == 'grok':
            # Placeholder for Grok API call
            return jsonify({'response': 'Grok API is not yet available.'})
        else:
            return jsonify({'error': 'Unsupported model'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
