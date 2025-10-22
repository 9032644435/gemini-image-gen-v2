import base64
import os
from flask import Flask, request, render_template_string
from google.cloud import aiplatform
# IMPORT GenerationConfig HERE
from vertexai.generative_models import GenerativeModel, GenerationConfig
from google.api_core import exceptions as gcp_exceptions

app = Flask(__name__)

# Initialize Vertex AI client using environment variables set by Cloud Run
try:
    # Your project and region vars are set via the Cloud Run ENV vars
    aiplatform.init(
        project=os.environ.get('GCP_PROJECT'), 
        location=os.environ.get('GCP_REGION', 'us-central1') 
    )
except Exception as e:
    print(f"Vertex AI initialization failed: {e}")


@app.route('/')
def index():
    # Simple HTML form
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Image Generation</title>
        <style>body { font-family: sans-serif; padding: 20px; }</style>
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
        model = GenerativeModel("imagen-3.0-generate-002")
        
        # --- THE FIX ---
        config = GenerationConfig(
            number_of_images=1 
        )
        
        result = model.generate_content(
            contents=[prompt],
            generation_config=config # <-- CORRECT ARGUMENT NAME
        )
        # --- END OF FIX ---
        
        # Check if the content was blocked by safety filters
        if not result.candidates or not result.candidates[0].content.parts:
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
        return f"Permission Denied: Ensure service account has roles. Error: {e}", 500
    except gcp_exceptions.ResourceExhausted as e:
        return f"Quota Exceeded (429): You hit the rate limit. Please wait or request a quota increase. Error: {e}", 429
    except Exception as e:
        return f"An unexpected error occurred: {e}", 500
