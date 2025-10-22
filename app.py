import base64
import os
from flask import Flask, request, render_template_string
from google.cloud import aiplatform
from vertexai.preview.vision_models import ImageGenerationModel

app = Flask(__name__)

# Initialize Vertex AI
aiplatform.init(project=os.environ.get('GCP_PROJECT'), location=os.environ.get('GCP_REGION'))

@app.route('/')
def index():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Image Generation</title>
    </head>
    <body>
        <form action="/generate-image" method="post">
            <label for="prompt">Enter a prompt:</label>
            <input type="text" id="prompt" name="prompt" required>
            <button type="submit">Generate Image</button>
        </form>
    </body>
    </html>
    """

@app.route('/generate-image', methods=['POST'])
def generate_image():
    prompt = request.form.get('prompt')
    if not prompt:
        return "Please provide a prompt.", 400

    try:
        model = ImageGenerationModel.from_pretrained("imagen-3.0-generate-002")
        images = model.generate_images(prompt=prompt, number_of_images=1)

        # Encode the image bytes to base64
        image_bytes = images[0]._image_bytes
        encoded_image = base64.b64encode(image_bytes).decode('utf-8')

        # Display the image
        return f'<img src="data:image/png;base64,{encoded_image}">'

    except Exception as e:
        return f"An error occurred: {e}", 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
