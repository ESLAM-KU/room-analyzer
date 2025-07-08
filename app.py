from flask import Flask, request, jsonify
import google.generativeai as genai
import mimetypes
import requests
import json
import re

app = Flask(__name__)

# إعداد Gemini
genai.configure(api_key="AIzaSyB4Rf8wINhYnBkeyQO_NKPHhh2WyotEDTs")
model = genai.GenerativeModel("gemini-1.5-pro")  # استخدم موديل مدعوم

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

Return JSON with only these keys (nothing more), and make sure each value is a single plain string:
- "main_items": "List of visible items, separated by commas"
- "estimated_area_sqm": "Like: 3m x 4m ≈ 12m²"
- "ventilation": "Good / Poor / No ventilation"
- "natural_light": "Strong / Moderate / Poor"
- "window_view": "Contains one/two window(s), optional outside view if visible"
- "rental_tips": "Suggestions to improve attractiveness"

Do not explain. Respond with raw JSON only.
"""

    try:
        gemini_response = model.generate_content([
            prompt,
            {"mime_type": mime_type, "data": image_bytes}
        ])

        raw_text = gemini_response.text.strip()

        # نحاول نطلع الـ JSON النظيف من النص
        match = re.search(r"```json\s*(\{.*?\})\s*```", raw_text, re.DOTALL)
        clean_json = match.group(1) if match else raw_text

        parsed = json.loads(clean_json)

        # نحتفظ فقط بالمفاتيح المطلوبة، ونتأكد إن القيم عبارة عن Strings
        allowed_keys = [
            "main_items",
            "estimated_area_sqm",
            "ventilation",
            "natural_light",
            "window_view",
            "rental_tips"
        ]

        result = {
            key: (
                ", ".join(value) if isinstance(value, list)
                else str(value)
            )
            for key, value in parsed.items()
            if key in allowed_keys
        }

        return jsonify(result)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
