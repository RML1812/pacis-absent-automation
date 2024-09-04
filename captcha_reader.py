import cv2
import numpy as np
import keras_ocr
from collections import Counter

# Function preprocess the CAPTCHA
def preprocess_captcha(img, num_colors=4):
    # Convert the image to RGB and then to a NumPy array
    image = np.array(img.convert("RGB"))
    
    # Reshape the image to a list of pixels
    pixels = image.reshape(-1, 3)
    
    # Apply K-Means clustering for color quantization
    from sklearn.cluster import KMeans

    kmeans = KMeans(n_clusters=num_colors, random_state=42)
    kmeans.fit(pixels)
    quantized_pixels = kmeans.cluster_centers_[kmeans.labels_].astype('uint8')
    quantized_image = quantized_pixels.reshape(image.shape)
    
    # Continue with the same steps as before using quantized_image
    pixels = quantized_image.reshape(-1, 3)
    pixel_tuples = [tuple(pixel) for pixel in pixels]
    color_counts = Counter(pixel_tuples)
    
    if not color_counts:
        raise ValueError("The input image has no colors.")
    
    most_common = color_counts.most_common(2)
    first_color = most_common[0][0]
    second_color = most_common[1][0] if len(most_common) > 1 else first_color
    
    print(f"First most frequent color: {first_color}")
    if len(most_common) > 1:
        print(f"Second most frequent color: {second_color}")
    else:
        print("Only one unique color found in the image.")
    
    mask_first = np.all(quantized_image == first_color, axis=-1)
    mask_second = np.all(quantized_image == second_color, axis=-1) if len(most_common) > 1 else np.zeros(quantized_image.shape[:2], dtype=bool)
    mask_other = ~(mask_first | mask_second)
    
    processed_image = quantized_image.copy()
    processed_image[mask_other] = first_color
    
    gray = cv2.cvtColor(processed_image, cv2.COLOR_RGB2GRAY)
    _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY_INV)
    
    kernel = np.ones((2, 1), np.uint8)
    closed_image = cv2.morphologyEx(thresh, cv2.MORPH_ERODE, kernel)
    
    return closed_image

# Function to perform OCR using Keras-OCR on an image from a URL
def read_captcha(img):
    # Preprocess the image from the URL
    processed_image = preprocess_captcha(img)
    
    # Convert the processed image to a format that Keras-OCR can handle
    image_np = cv2.cvtColor(processed_image, cv2.COLOR_GRAY2RGB)
    
    # Initialize the Keras-OCR pipeline
    pipeline = keras_ocr.pipeline.Pipeline()
    
    # Perform OCR on the image
    prediction_groups = pipeline.recognize([image_np])
    
    # Extract the text from the predictions
    captcha_text = ' '.join([text for text, box in prediction_groups[0]])
    
    return captcha_text