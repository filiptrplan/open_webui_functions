import requests
from dotenv import load_dotenv
import os
import base64
from io import BytesIO
from PIL import Image
import re

load_dotenv()

api_token = os.getenv("VENICE_API_TOKEN")
headers = {"Authorization": f"Bearer {api_token}", "Content-Type": "application/json"}


def get_models_from_env():
    """Retrieves models from the VENICE_MODELS environment variable."""
    models_str = os.getenv("VENICE_MODELS")
    if models_str:
        model_ids = [model_id.strip() for model_id in models_str.split(",")]
        return [{"id": model_id, "type": "image"} for model_id in model_ids]
    else:
        return []


def get_models_from_api():
    """Retrieves available models from the Venice.ai API."""
    url = "https://api.venice.ai/api/v1/models"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()["data"]
    else:
        print(f"Failed to retrieve models from API: {response.status_code}")
        return []


def get_models():
    """Gets models from ENV or API, prioritizing ENV."""
    models = get_models_from_env()
    if not models:
        models = get_models_from_api()
    return models


def choose_model(models):
    """Allows the user to select a model from the available list."""
    print("Available models:")
    image_models = [model for model in models if model.get("type") == "image"]
    for i, model in enumerate(image_models):
        print(f"{i + 1}. {model['id']}")
    while True:
        try:
            choice = int(input("Select a model by its number: "))
            if 1 <= choice <= len(image_models):
                return image_models[choice - 1]["id"]
            else:
                print("Invalid choice. Please enter a number from the list.")
        except ValueError:
            print("Invalid input. Please enter a number.")


def generate_image(prompt, model, width=512, height=512, negative_prompt=""):
    """Generates an image using the Venice.ai API."""
    url = "https://api.venice.ai/api/v1/image/generate"
    payload = {
        "model": model,
        "prompt": prompt,
        "width": width,
        "height": height,
        "steps": 16,
        "hide_watermark": True,
        "return_binary": False,
        "cfg_scale": 4,
        "negative_prompt": negative_prompt,
        "safe_mode": False,
    }
    response = requests.post(url, json=payload, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Image generation failed: {response.status_code}")
        return None


def sanitize_filename(filename):
    """Sanitizes a string to be safe for use as a filename."""
    return re.sub(r"[^\w\s-]", "", filename).strip()


def display_and_save_image(image_data, model, prompt):
    """Displays and saves the generated image."""
    if image_data and "images" in image_data:
        images_dir = "./images"
        os.makedirs(images_dir, exist_ok=True)
        sanitized_prompt = sanitize_filename(prompt)
        for i, image_str in enumerate(image_data["images"]):
            image_bytes = base64.b64decode(image_str)
            image = Image.open(BytesIO(image_bytes))
            image.show()
            filename = (
                f"{images_dir}/{sanitize_filename(model)}_{sanitized_prompt}_{i}.png"
            )
            image.save(filename)
            print(f"Image saved to {filename}")
    else:
        print("No image data found.")


# Example usage:
if __name__ == "__main__":
    models = get_models()
    selected_model = choose_model(models)
    prompt = input("Enter your prompt: ")
    image_data = generate_image(prompt, selected_model)
    display_and_save_image(image_data, selected_model, prompt)
