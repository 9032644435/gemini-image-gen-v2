import base64
import os
import logging
from flask import Flask, request, jsonify
from google.cloud import aiplatform
from vertexai.preview.vision_models import ImageGenerationModel

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

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
                background-color: #333;
                color: #fff;
                display: flex;
                flex-direction: column;
                align-items: center;
                padding-top: 50px;
                margin: 0;
                transition: filter 0.3s ease-in-out;
            }
            .container {
                background-color: #444;
                padding: 30px;
                border-radius: 8px;
                box-shadow: 0 4px 8px rgba(0, 0, 0, 0.3);
                width: 90%;
                max-width: 600px;
                text-align: center;
            }
            form {
                display: flex;
                flex-direction: column;
                gap: 15px;
            }
            input, select {
                padding: 10px;
                border: 1px solid #555;
                background-color: #555;
                color: #fff;
                border-radius: 4px;
                font-size: 16px;
            }
            button {
                padding: 12px;
                background-color: #007BFF;
                color: white;
                border: none;
                border-radius: 4px;
                cursor: pointer;
                font-size: 16px;
                transition: background-color 0.3s;
            }
            button:hover {
                background-color: #0056b3;
            }
            #loading {
                display: none;
                margin-top: 20px;
            }
            #results-container {
                margin-top: 20px;
                display: flex;
                flex-wrap: wrap;
                gap: 15px;
                justify-content: center;
            }
            .result-item {
                display: flex;
                flex-direction: column;
                align-items: center;
                gap: 10px;
            }
            .result-item img {
                max-width: 100%;
                border-radius: 4px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.2);
            }
            .download-btn {
                background-color: #28a745;
            }
            .download-btn:hover {
                background-color: #218838;
            }
            #media-upload-area {
                margin-top: 20px;
                padding: 20px;
                border: 2px dashed #555;
                border-radius: 8px;
                text-align: center;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h2>Generate Image (Imagen 3.0)</h2>
            <form id="generate-form" enctype="multipart/form-data">
                <label for="prompt" style="text-align: left;">Enter a descriptive prompt:</label>
                <input type="text" id="prompt" name="prompt" required placeholder="A cyberpunk cat on a neon rooftop...">

                <label for="image_count" style="text-align: left;">Number of images:</label>
                <select id="image_count" name="image_count">
                    <option value="1">1</option>
                    <option value="2">2</option>
                    <option value="3">3</option>
                </select>

                <label for="aspect_ratio" style="text-align: left;">Aspect Ratio:</label>
                <select id="aspect_ratio" name="aspect_ratio">
                    <option value="1:1">1:1</option>
                    <option value="16:9">16:9</option>
                    <option value="9:16">9:16</option>
                    <option value="3:4">3:4</option>
                </select>

                <div id="media-upload-area">
                    <label for="upload_file" style="text-align: left;">Upload Media (for editing):</label>
                    <input type="file" id="upload_file" name="upload_file">
                </div>

                <button type="submit">Generate Image</button>
            </form>
            <div id="loading">Loading...</div>
            <div id="results-container"></div>
        </div>

        <script>
            $(document).ready(function() {
                $('#generate-form').on('submit', function(e) {
                    e.preventDefault();

                    var formData = new FormData(this);

                    $('body').css('filter', 'blur(5px)');
                    $('#loading').show();
                    $('#results-container').empty();

                    $.ajax({
                        type: 'POST',
                        url: '/generate-image',
                        data: formData,
                        processData: false,
                        contentType: false,
                        success: function(data) {
                            $('body').css('filter', 'none');
                            $('#loading').hide();
                            if (data.error) {
                                $('#results-container').html('<p>Error: ' + data.error + '</p>');
                            } else {
                                $.each(data.images, function(index, base64_image) {
                                    var resultItem = $('<div class="result-item"></div>');
                                    resultItem.append('<img src="data:image/png;base64,' + base64_image + '">');
                                    var downloadBtn = $('<button class="download-btn">Download Image</button>');
                                    downloadBtn.on('click', function() {
                                        var a = document.createElement('a');
                                        a.href = 'data:image/png;base64,' + base64_image;
                                        a.download = 'generated_image_' + index + '.png';
                                        a.click();
                                    });
                                    resultItem.append(downloadBtn);
                                    $('#results-container').append(resultItem);
                                });
                            }
                        },
                        error: function(jqXHR, textStatus, errorThrown) {
                            $('body').css('filter', 'none');
                            $('#loading').hide();
                            var errorMsg = 'An unexpected error occurred.';
                            if (jqXHR.responseJSON && jqXHR.responseJSON.error) {
                                errorMsg = 'Error: ' + jqXHR.responseJSON.error;
                            }
                            $('#results-container').html('<p>' + errorMsg + '</p>');
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
    if 'upload_file' in request.files and request.files['upload_file'].filename != '':
        logging.info("Received user image for editing.")
        return jsonify({'error': 'Image editing is not yet fully implemented for this version. Please use the text prompt only.'}), 400

    prompt = request.form.get('prompt')
    try:
        image_count = int(request.form.get('image_count', 1))
    except (ValueError, TypeError):
        image_count = 1

    aspect_ratio = request.form.get('aspect_ratio', '1:1')

    if not prompt:
        return jsonify({'error': 'Please provide a prompt.'}), 400

    try:
        model = ImageGenerationModel.from_pretrained("imagen-3.0-generate-002")

        response = model.generate_images(
            prompt=prompt,
            number_of_images=image_count,
            aspect_ratio=aspect_ratio
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
