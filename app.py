import base64
import os
from flask import Flask, request, render_template_string
from google.cloud import aiplatform
from vertexai.generative_models import GenerativeModel
from google.api_core import exceptions as gcp_exceptions

app = Flask(__name__)

# Initialize Vertex AI client using environment variables set by Cloud Run
# This relies on the 'Vertex AI User' role you assigned to the Service Account.
try:
    aiplatform.init(
        project=os.environ.get('GCP_PROJECT'), 
        location=os.environ.get('GCP_REGION', 'us-central1') # Provide a fallback region
    )
except Exception as e:
    # Log initialization errors but continue, Gunicorn will catch severe issues
    print(f"Vertex AI initialization failed: {e}")


@app.route('/')
def index():
    # Render a simple HTML form for the user prompt
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Gemini Image Generation</title>
        <style>
            body { font-family: sans-serif; padding: 20px; }
            form { display: flex; flex-direction: column; width: 300px; }
            input[type="text"] { margin-bottom: 10px; padding: 8px; }
            button { padding: 10px; cursor: pointer; }
        </style>
    </head>
    <body>
        <h2>Generate Image (Imagen 3.0)</h2>
        <form action="/generate-image" method="post">
            <label for="prompt">Enter a descriptive prompt:</label>
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
        # 1. Use the GenerativeModel class for image generation
        model = GenerativeModel("imagen-3.0-generate-002")
        
        # 2. Call the generate_content method
        result = model.generate_content(
            contents=[prompt],
            config={"number_of_images": 1}
        )
        
        # Check if the content was blocked by safety filters
        if not result.candidates or not result.candidates[0].content.parts:
            # Check for block reason
            feedback = result.prompt_feedback.block_reason.name if result.prompt_feedback else "Unknown"
            return f"Image generation failed. Reason: Prompt was blocked by safety filters ({feedback}). Try a different prompt.", 403

        # Retrieve the image bytes from the response part
        image_part = result.candidates[0].content.parts[0]
        image_bytes = image_part.inline_data.data
        
        # Encode the image bytes to base64
        encoded_image = base64.b64encode(image_bytes).decode('utf-8')

        # Display the image
        return f'<h2>Prompt: {prompt}</h2><img src="data:image/png;base64,{encoded_image}">'

    except gcp_exceptions.PermissionDenied as e:
        return f"Permission Denied: Ensure your service account has the 'Vertex AI User' role. Error: {e}", 500
    except gcp_exceptions.ResourceExhausted as e:
        return f"Quota Exceeded (429): You hit the rate limit. Please wait or request a quota increase. Error: {e}", 429
    except Exception as e:
        return f"An unexpected error occurred during API call: {e}", 500

# Note: The if __name__ == '__main__' block is removed as Gunicorn manages the app start.
