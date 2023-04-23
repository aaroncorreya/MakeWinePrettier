from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    send_from_directory,
)
from werkzeug.utils import secure_filename
import os
import requests
import base64

app = Flask(__name__)

app.config["UPLOAD_FOLDER"] = "uploads"
app.config["ALLOWED_EXTENSIONS"] = {"png", "jpg", "jpeg", "gif"}

# Create the uploads folder if it doesn't exist
if not os.path.exists(app.config["UPLOAD_FOLDER"]):
    os.makedirs(app.config["UPLOAD_FOLDER"])


@app.route("/uploads/<filename>")
def uploaded_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)


def allowed_file(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in app.config["ALLOWED_EXTENSIONS"]
    )


def generate_image(wine_data):
    engine_id = "stable-diffusion-v1-5"
    api_host = "https://api.stability.ai"

    # Replace YOUR_API_KEY with your actual API key from Stability.AI
    api_key = "sk-Vl3z9R7KAXZwBmyBlbovD7kKS3uMSHrg7WX46ySJzY3TEm78"

    # Prepare the description text for the image
    prompt = f"Change the wine color in the photo to {wine_data['wine_type']} wine with {wine_data['clarity']} clarity, {wine_data['intensity']} intensity, and {wine_data['color']} color."

    # Read the uploaded image and encode it in base64
    with open(wine_data["wine_image_path"], "rb") as image_file:
        encoded_image = base64.b64encode(image_file.read()).decode("utf-8")

    # Make the API call
    response = requests.post(
        f"{api_host}/v1/generation/{engine_id}/image-to-image",
        headers={"Accept": "application/json", "Authorization": f"Bearer {api_key}"},
        files={"init_image": open(wine_data["wine_image_path"], "rb")},
        data={
            "image_strength": 0.35,
            "text_prompts[0][text]": prompt,
        },
    )

    if response.status_code != 200:
        raise Exception("Non-200 response: " + str(response.text))

    if response.status_code == 200:
        # Save the generated image to a file
        image_path = os.path.join(app.config["UPLOAD_FOLDER"], "generated_image.jpg")
        with open(image_path, "wb") as image_file:
            image_file.write(response.content)

        return image_path

    return None


@app.route("/", methods=["GET", "POST"])
def index():
    wine_data = None

    if request.method == "POST":
        wine_data = {
            "clarity": request.form["clarity"],
            "intensity": request.form["intensity"],
            "color": request.form["color"],
            "wine_type": request.form["wine_type"],
        }

        if "wine_image" in request.files:
            wine_image = request.files["wine_image"]
            if wine_image and allowed_file(wine_image.filename):
                filename = secure_filename(wine_image.filename)
                file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
                wine_image.save(file_path)
                wine_data["wine_image_path"] = file_path

        # Call the generate_image function
        generated_image_path = generate_image(wine_data)
        if generated_image_path:
            generated_image = f"/uploads/{os.path.basename(generated_image_path)}"

    return render_template(
        "index.html", wine_data=wine_data, generated_image=generated_image
    )


if __name__ == "__main__":
    app.run(debug=True)
