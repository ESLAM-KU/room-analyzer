from flask import Flask, request, jsonify
import google.generativeai as genai
import mimetypes
import requests
import json
import re

app = Flask(__name__)

# اعداد Gemini
genai.configure(api_key="AIzaSyB4RF8wINhYnBkeyQO_NKPHHh2WyotEDTs")
model = genai.GenerativeModel("gemini-2.5-flash")

@app.route('/')
def home():
    return {"message": "✅ Room Analyzer API is Running"}

@app.route('/extract', methods=['POST'])
def extract_info():
    data = request.get_json()
    if not data or 'image_url' not in data:
        return jsonify({"error": "Missing 'image_url' in request"}), 400

    image_url = data['image_url']

    try:
        response = requests.get(image_url)
        response.raise_for_status()
        image_bytes = response.content

        mime_type = response.headers.get("Content-Type", "")
        if not mime_type.startswith("image/"):
            return jsonify({"error": "Provided URL is not an image"}), 400

    except Exception as e:
        return jsonify({"error": f"Failed to fetch image: {str(e)}"}), 400

    prompt = """
You are a smart assistant helping users analyze a rental room from an image.

Return JSON with the following keys, ensuring all values are single strings and not lists:
- "main_items": "List of visible items, separated by commas"
- "estimated_area_sqm": "Like: 3m x 4m ≈ 12m²"
- "ventilation": "Good / Poor / No ventilation"
- "natural_light": "Strong / Moderate / Poor"
- "window_view": "Contains one/two window(s), optional outside view if visible"
- "rental_tips": "Suggestions to improve attractiveness""""

    image_part = {
        'mime_type': mime_type,
        'data': image_bytes
    }

    try:
        response = model.generate_content([prompt, image_part])
        response.resolve()
        
        # Extract JSON string from response text
        json_match = re.search(r'```json\n(.*?)```', response.text, re.DOTALL)
        if json_match:
            json_string = json_match.group(1)
            result = json.loads(json_string)
        else:
            # If no ```json``` block, try to parse the whole response as JSON
            result = json.loads(response.text)

        return jsonify(result)

    except Exception as e:
        return jsonify({"error": f"Failed to analyze image: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
