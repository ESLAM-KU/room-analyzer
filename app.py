from flask import Flask, request, jsonify
import google.generativeai as genai
import requests

app = Flask(__name__)

# إعداد مفتاح API
genai.configure(api_key="YOUR_GEMINI_API_KEY")
model = genai.GenerativeModel("gemini-2.5-flash")

@app.route('/')
def home():
    return """
    <h3>✅ Room Description API is Running</h3>
    <p>Send a POST request to <code>/describe</code> with JSON containing an <code>image_url</code>.</p>
    """

@app.route('/describe', methods=['POST'])
def describe_room():
    data = request.get_json()
    image_url = data.get('image_url')

    if not image_url:
        return jsonify({'error': 'Missing image_url in request'}), 400

    try:
        image_response = requests.get(image_url)
        image_response.raise_for_status()
        image_bytes = image_response.content

    except Exception as e:
        return jsonify({'error': f'Failed to download image: {str(e)}'}), 400

    prompt = """
    You are a real estate assistant. Analyze this image and give a detailed structured JSON describing the room for potential rental listing. Focus on clarity and usefulness.

    Your output must follow this structure **exactly** in English:

    {
      "room_type": "[Bedroom / Kitchen / Living Room / Bathroom / Balcony / Unknown]",
      "main_items": "[Key visible furniture or appliances]",
      "estimated_dimensions_m": "[Length x Width in meters (e.g., 3.5m x 4m)]",
      "estimated_area_sqm": "[Approximate area in square meters (e.g., 14 sqm)]",
      "condition": "[Excellent / Good / Average / Poor]",
      "natural_light": "[Yes / No / Partial]",
      "window_count": "[Number of windows visible in image (e.g., 1 or 2)]",
      "floor_type": "[Tiles / Wood / Carpet / Concrete / Other]",
      "wall_condition": "[Painted / Needs repair / Stained / Clean]",
      "ventilation": "[AC / Fan / Window only / None]",
      "rental_tips": "[Useful suggestion to improve the room’s rental appeal]"
    }

    ❗ Notes:
    - Do not include any extra commentary or explanations outside the JSON.
    - Assume this is an Egyptian apartment — use meter units only.
    - If the room is unclear or unknown, fill with 'Unknown' but still return valid JSON keys.
    """

    try:
        response = model.generate_content([
            prompt,
            {
                "mime_type": "image/jpeg",
                "data": image_bytes
            }
        ])
        return jsonify({'analysis': response.text.strip()})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
