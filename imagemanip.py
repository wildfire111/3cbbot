from PIL import Image
import io
import os
import requests

def combine_and_resize_images(image_urls):
    """
    Combines multiple images from URLs horizontally and resizes the result to a width of 200px while preserving the aspect ratio.
    Images are checked for existence in the /images directory and downloaded if not found.
    """
    images = []
    os.makedirs('images', exist_ok=True)  # Ensure the /images directory exists

    try:
        for url in image_urls:
            # Extract the image filename from the URL
            image_name = url.split('/')[-1]
            image_path = os.path.join('images', image_name)

            if not os.path.exists(image_path):
                # Download the image if it doesn't exist
                response = requests.get(url)
                response.raise_for_status()  # Raise an error for bad responses

                # Save the image to the /images directory
                with open(image_path, 'wb') as f:
                    f.write(response.content)

            # Open the image from the directory
            image = Image.open(image_path)
            images.append(image)
    except requests.exceptions.RequestException as e:
        print(f"Error downloading image: {e}")
        return None

    # Calculate total width and max height for the new combined image
    total_width = sum(image.width for image in images)
    max_height = max(image.height for image in images)

    # Create a new image with the calculated dimensions
    combined_image = Image.new('RGB', (total_width, max_height))

    # Paste each image next to each other in the combined image
    x_offset = 0
    for image in images:
        combined_image.paste(image, (x_offset, 0))
        x_offset += image.width
        image.close()  # Close the image to release memory

    # Resize the combined image
    new_width = 500
    aspect_ratio = combined_image.height / combined_image.width
    new_height = int(new_width * aspect_ratio)
    resized_image = combined_image.resize((new_width, new_height), Image.LANCZOS)

    return resized_image

def image_to_bytes(image):
    """
    Converts a PIL image to a bytes object for Discord file uploading.
    """
    image_bytes = io.BytesIO()
    image.save(image_bytes, format='PNG')
    image_bytes.seek(0)  # Move the pointer to the start of the BytesIO object
    return image_bytes
