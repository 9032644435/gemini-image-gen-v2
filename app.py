import base64
import os
from flask import Flask, request
from google.cloud import aiplatform
from vertexai.generative_models import GenerativeModel

app = Flask(__name__)

# Initialize Vertex AI
aiplatform.init(project=os.environ.get('GCP_PROJECT'), location=os.environ.get('GCP_REGION'))

@app.route('/')
def index():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Gemini Image Generation</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">

        <style>
            body {
                font-family: Arial, sans-serif;
                background-color: #f0f0f0;
                display: flex;
                flex-direction: column;
                align-items: center;
                padding-top: 50px;
                margin: 0;
            }
            .container {
                background-color: white;
                padding: 30px;
                border-radius: 8px;
                box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
                width: 90%;
                max-width: 500px;
                text-align: center;
            }
            form {
                display: flex;
                flex-direction: column;
                gap: 15px;
            }
            input[type="text"] {
                padding: 10px;
                border: 1px solid #ccc;
                border-radius: 4px;
                font-size: 16px;
            }
            button {
                padding: 10px;
                background-color: #4CAF50; /* Green */
                color: white;
                border: none;
                border-radius: 4px;
                cursor: pointer;
                font-size: 16px;
                transition: background-color 0.3s;
            }
            button:hover {
                background-color: #45a049;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h2>Generate Image (Imagen 3.0)</h2>
            <form action="/generate-image" method="post">
                <label for="prompt" style="text-align: left;">Enter a descriptive prompt:</label>
                <input type="text" id="prompt" name="prompt" required placeholder="A cyberpunk cat on a neon rooftop...">
                <button type="submit">Generate Image</button>
            </form>
        </div>
    </body>
    </html>
    """

@app.route('/generate-image', methods=['POST'])
def generate_image():
    prompt = request.form.get('prompt')
    if not prompt:
        return "Please provide a prompt.", 400

    try:
        model = GenerativeModel("imagen-3.0-generate-002")

        response = model.generate_content([prompt])

        # Extract image bytes from the first candidate
        image_bytes = response.candidates[0].content.parts[0].image._image_bytes

        # Encode the image bytes to base64
        encoded_image = base64.b64encode(image_bytes).decode('utf-8')

        # Display the image
        return f'<img src="data:image/png;base64,{encoded_image}">'

    except Exception as e:
        return f"An error occurred: {e}", 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
