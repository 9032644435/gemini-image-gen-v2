import base64
import os
from flask import Flask, request, jsonify
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
        <title>Gemini Image Generation</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <script src="https://ajax.googleapis.com/ajax/libs/jquery/3.5.1/jquery.min.js"></script>
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
            input[type="text"], select {
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
            #loading {
                display: none;
                margin-top: 20px;
            }
            #results-container {
                margin-top: 20px;
                display: flex;
                flex-wrap: wrap;
                gap: 10px;
                justify-content: center;
            }
            #results-container img {
                max-width: 100%;
                border-radius: 4px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h2>Generate Image (Imagen 3.0)</h2>
            <form id="generate-form">
                <label for="prompt" style="text-align: left;">Enter a descriptive prompt:</label>
                <input type="text" id="prompt" name="prompt" required placeholder="A cyberpunk cat on a neon rooftop...">

                <label for="image_count" style="text-align: left;">Number of images:</label>
                <select id="image_count" name="image_count">
                    <option value="1">1</option>
                    <option value="2">2</option>
                    <option value="3">3</option>
                </select>

                <button type="submit">Generate Image</button>
            </form>
            <div id="loading">Loading...</div>
            <div id="results-container"></div>
        </div>

        <script>
            $(document).ready(function() {
                $('#generate-form').on('submit', function(e) {
                    e.preventDefault();

                    var formData = {
                        'prompt': $('#prompt').val(),
                        'image_count': $('#image_count').val()
                    };

                    $('#loading').show();
                    $('#results-container').empty();

                    $.ajax({
                        type: 'POST',
                        url: '/generate-image',
                        data: formData,
                        dataType: 'json',
                        success: function(data) {
                            $('#loading').hide();
                            if (data.error) {
                                $('#results-container').html('<p>Error: ' + data.error + '</p>');
                            } else {
                                $.each(data.images, function(index, base64_image) {
                                    $('#results-container').append('<img src="data:image/png;base64,' + base64_image + '">');
                                });
                            }
                        },
                        error: function() {
                            $('#loading').hide();
                            $('#results-container').html('<p>An unexpected error occurred.</p>');
                        }
                    });
                });
            });
        </script>
    </body>
    </html>
    """

@app.route('/generate-image', methods=['POST'])
def generate_image():
    prompt = request.form.get('prompt')
    try:
        image_count = int(request.form.get('image_count', 1))
    except (ValueError, TypeError):
        image_count = 1

    if not prompt:
        return jsonify({'error': 'Please provide a prompt.'}), 400

    try:
        model = ImageGenerationModel.from_pretrained("imagen-3.0-generate-002")

        response = model.generate_images(
            prompt=prompt,
            number_of_images=image_count
        )

        images_b64 = []
        for image in response:
            image_bytes = image._image_bytes
            encoded_image = base64.b64encode(image_bytes).decode('utf-8')
            images_b64.append(encoded_image)

        return jsonify({'images': images_b64})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
