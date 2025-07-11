from flask import Flask, render_template, request, Response, redirect, url_for
import cv2
import imagehash
from PIL import Image
import pandas as pd
from urllib.parse import urlparse, parse_qs
import os
import io

from pokemontcgmanager.card import Card


# Helper Functions


def print_stats(card: dict):
    """
    Print basic statistics of a Pokémon card.

    Args:
        card (dict): Dictionary representing the Pokémon card.
    """
    print(
        card["id"],
        card["name"],
        card.get("cardmarket")["prices"]["averageSellPrice"],
        card.get("cardmarket")["updatedAt"],
    )


def preprocess_image(img: Image) -> Image:
    """
    Preprocess image for better hash comparison.
    
    Args:
        img (PIL.Image): Input image
        
    Returns:
        PIL.Image: Preprocessed image
    """
    # Convert to RGB if needed
    if img.mode != 'RGB':
        img = img.convert('RGB')
    
    # Resize to standard card dimensions (maintain aspect ratio)
    target_width = 600
    target_height = 825
    
    # Calculate resize ratio to maintain aspect ratio
    img_ratio = img.width / img.height
    target_ratio = target_width / target_height
    
    if img_ratio > target_ratio:
        # Image is wider, fit to height
        new_height = target_height
        new_width = int(target_height * img_ratio)
    else:
        # Image is taller, fit to width
        new_width = target_width
        new_height = int(target_width / img_ratio)
    
    img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
    
    # Crop to target dimensions if larger
    if new_width > target_width or new_height > target_height:
        left = (new_width - target_width) // 2
        top = (new_height - target_height) // 2
        right = left + target_width
        bottom = top + target_height
        img = img.crop((left, top, right, bottom))
    
    return img

def get_hashes(img: Image) -> dict:
    """
    Calculate various types of hashes for an image.

    Args:
        img (PIL.Image): Image to calculate hashes for.

    Returns:
        dict: Dictionary with various hash types (perceptual, difference, wavelet, color).
    """
    # Preprocess the image first
    img = preprocess_image(img)
    
    perceptual = imagehash.phash(img, 32, 8)
    difference = imagehash.dhash(img, 32)
    wavelet = imagehash.whash(img, 32)
    color = imagehash.colorhash(img)
    return {
        "perceptual": perceptual,
        "difference": difference,
        "wavelet": wavelet,
        "color": color,
    }


def adjust_query(query: str) -> str:
    """
    Adjusts the search query to ensure that 'name:"nombre"' format has the name in uppercase,
    or converts the name to uppercase if 'name:nombre' format is found.
    It also ensures that other Lucene operators remain unchanged.

    Args:
        query (str): The original search query.

    Returns:
        str: The adjusted search query with 'name:"NOMBRE"' format if 'name:"nombre"' format is found,
             or with 'name:NOMBRE' format if 'name:nombre' format is found, preserving other Lucene operators.
    """
    first_query = query.split()[0]
    if "name:" not in query and ":" not in first_query:
        query = query[0].upper() + query[1:]
        query = f"name:{query}"
    return query


card_hashes = pd.read_pickle("card_hashes_32b.pickle")


app = Flask(__name__)

img_height = 825
img_width = 600
aspect_ratio = img_height / img_width

rect_height = img_height // 2
rect_width = img_width // 2

# Initialize video capture
cap = cv2.VideoCapture(0)

# Check if camera opened successfully
if not cap.isOpened():
    print("Warning: Could not open camera. Camera functionality will be disabled.")
    cap = None
    width = 800
    height = 600
else:
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) * 1.4)
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) * 1.4)

rect_x = (width - rect_width) // 2
rect_y = (height - rect_height) // 2

rect_color = (0, 255, 0)
border = 2


def capture_image() -> Image or None:
    """
    Capture an image from the camera.

    Returns:
        PIL.Image or None: Captured image as a PIL Image or None if capture fails.
    """
    if cap is None:
        return None
    
    success, frame = cap.read()
    if success and frame is not None and frame.size > 0:
        frame = cv2.resize(frame, (0, 0), fx=1.4, fy=1.4)
        my_card_frame = frame[
            rect_y : rect_y + rect_height, rect_x : rect_x + rect_width
        ]
        my_card_img = Image.fromarray(my_card_frame)
        return my_card_img
    return None


def get_most_similar(img: Image, hash_type="perceptual", n=1):
    """
    Find the most similar Pokémon card based on image hash.

    Args:
        img (PIL.Image): Image to compare with the Pokémon card database.
        hash_type (str): Type of hash to use (perceptual, difference, wavelet, color).
        n (int): Number of similar cards to retrieve.

    Returns:
        str or list: ID(s) of the most similar Pokémon card(s).
    """
    hashes_dict = get_hashes(img)
    
    # Calculate distances for all hash types
    distances = {}
    for hash_name in ["perceptual", "difference", "wavelet"]:
        if hash_name in card_hashes.columns:
            card_hashes[f"{hash_name}_distance"] = card_hashes[hash_name] - hashes_dict[hash_name]
            card_hashes[f"{hash_name}_distance"] = card_hashes[f"{hash_name}_distance"].astype("int")
            distances[hash_name] = card_hashes[f"{hash_name}_distance"]
    
    # Use the specified hash type as primary
    primary_distance = distances.get(hash_type, distances["perceptual"])
    
    # Calculate confidence score (lower distance = higher confidence)
    max_distance = primary_distance.max()
    confidence_scores = 1 - (primary_distance / max_distance)
    
    # Filter for high confidence matches (distance < 50% of max)
    high_confidence_mask = primary_distance < (max_distance * 0.5)
    
    if high_confidence_mask.sum() > 0:
        # Use only high confidence matches
        filtered_hashes = card_hashes[high_confidence_mask]
        filtered_distances = primary_distance[high_confidence_mask]
        filtered_confidence = confidence_scores[high_confidence_mask]
    else:
        # If no high confidence matches, use all
        filtered_hashes = card_hashes
        filtered_distances = primary_distance
        filtered_confidence = confidence_scores
    
    # Sort by distance (lowest first)
    sorted_indices = filtered_distances.argsort()
    
    if n > 1:
        top_indices = sorted_indices[:n]
        similar_ids = filtered_hashes.iloc[top_indices]["id"].tolist()
        return similar_ids
    else:
        best_index = sorted_indices[0]
        similar_id = filtered_hashes.iloc[best_index]["id"]
        confidence = filtered_confidence.iloc[best_index]
        
        # Print confidence for debugging
        print(f"Best match confidence: {confidence:.2%}")
        
        return similar_id


# Routes and Views


@app.route("/")
def index():
    """
    Main route that displays the homepage.
    """
    return render_template("index.html")


@app.route("/detect_card")
def detect_card():
    return render_template("detector.html")

@app.route("/upload_image", methods=["POST"])
def upload_image():
    if "file" not in request.files:
        return Response("No file uploaded", status=400)
    
    file = request.files["file"]
    if file.filename == "":
        return Response("No file selected", status=400)
    
    if file:
        # Read the image
        img_data = file.read()
        img = Image.open(io.BytesIO(img_data))
        
        # Get the hash type from the request
        hash_type = request.form.get("hash_type", "perceptual")
        
        # Get multiple potential matches
        similar_ids = get_most_similar(img, hash_type, n=5)
        
        # Get card details for all matches
        similar_cards = []
        for card_id in similar_ids:
            try:
                card = Card.find(card_id)
                similar_cards.append(card)
            except:
                continue
        
        if similar_cards:
            # Return the best match as primary result
            best_card = similar_cards[0]
            print_stats(best_card)
            
            # Return template with multiple options
            return render_template("pokemon_card_matches.html", 
                                 primary_card=best_card, 
                                 all_matches=similar_cards)
        else:
            return Response("No matches found", status=404)
    
    return Response("Error processing image", status=400)


@app.route("/search", methods=["GET", "POST"])
def search_card():
    if request.method == "POST":
        search_query = request.form["search"]
        print(search_query)
        query = adjust_query(search_query)
        # Redirect to the '/cards?q={search_query}' route after submitting the form
        print(query)
        return redirect(url_for("cards", q=query))

    return render_template("search.html")


@app.route("/cards")
def cards():
    # check if there is any htmx request
    if request.headers.get("HX-Boosted") == "true":
        # get the target page from requests attributes
        page = int(request.args.get("target-page"))
        page = page if page > 0 else 1
        # get the url from the request
        url = request.headers.get("HX-Current-URL")

        # parse the url to get the query string
        parsed = urlparse(url)
        query_string = parse_qs(parsed.query)

        # get the search query from the query string
        search_query = query_string["q"][0]

        # get the page size from the query string
        page_size = query_string["page_size"][0] if "page_size" in query_string else 20

        response = Card.where(q=search_query, pageSize=page_size, page=page)
        # Check if there are more pages getting the first card of the next page
        last_card = page_size * page
        next_card = Card.where(q=search_query, pageSize=1, page=last_card + 1)
        last_page = len(next_card) == 0
        return render_template(
            "filtered_cards.html",
            cards=response,
            last_page=last_page,
            page=page,
        )

    search_query = request.args.get("q", None)
    page_size = request.args.get("page_size", 20)
    page = 1

    response = Card.where(q=search_query, pageSize=page_size, page=page)
    # Check if there are more pages getting the first card of the next page
    last_card = page_size * page
    next_card = Card.where(q=search_query, pageSize=1, page=last_card + 1)
    last_page = len(next_card) == 0

    return render_template(
        "filtered_cards.html",
        cards=response,
        last_page=last_page,
        page=page,
    )


@app.route("/card/<card_id>")
def card_page(card_id: str):
    response = Card.find(card_id)
    return render_template("card_page.html", pokemon=response)


@app.route("/about")
def about():
    return render_template("about.html")


# Functions for generating and streaming video frames


def generate_frames():
    while True:
        success, frame = cap.read()
        if not success:
            break
        else:
            ret, buffer = cv2.imencode(".jpg", frame)
            if not ret:
                continue
            frame = buffer.tobytes()
            yield (b"--frame\r\n" b"Content-Type: image/jpeg\r\n\r\n" + frame + b"\r\n")


@app.route("/video_feed")
def video_feed():
    def generate():
        if cap is None:
            # Return a placeholder image when camera is not available
            import numpy as np
            placeholder = np.zeros((600, 800, 3), dtype=np.uint8)
            cv2.putText(placeholder, "Camera Not Available", (200, 300), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            cv2.putText(placeholder, "Please use image upload", (150, 350), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            ret, buffer = cv2.imencode(".jpg", placeholder)
            frame = buffer.tobytes()
            yield (b"--frame\r\n" b"Content-Type: image/jpeg\r\n\r\n" + frame + b"\r\n")
            return
            
        while True:
            success, frame = cap.read()
            if not success or frame is None or frame.size == 0:
                break
                
            # Remove the horizontal flip - frame = cv2.flip(frame, 1)
            frame = cv2.resize(frame, (0, 0), fx=1.4, fy=1.4)
            cv2.rectangle(
                frame,
                (rect_x, rect_y),
                (rect_x + rect_width, rect_y + rect_height),
                rect_color,
                border,
            )

            ret, buffer = cv2.imencode(".jpg", frame)
            if not ret:
                continue
            frame = buffer.tobytes()
            yield (b"--frame\r\n" b"Content-Type: image/jpeg\r\n\r\n" + frame + b"\r\n")

    return Response(generate(), mimetype="multipart/x-mixed-replace; boundary=frame")


# Routes for comparing images and displaying similar Pokémon cards


@app.route("/perceptual_hash")
def perceptual():
    img = capture_image()
    if img is None:
        return Response(status=204)

    similar_ids = get_most_similar(img, "perceptual", n=3)
    
    # Get card details for matches
    similar_cards = []
    for card_id in similar_ids:
        try:
            card = Card.find(card_id)
            similar_cards.append(card)
        except:
            continue
    
    if similar_cards:
        best_card = similar_cards[0]
        print_stats(best_card)
        
        return render_template("pokemon_card_matches.html", 
                             primary_card=best_card, 
                             all_matches=similar_cards)
    
    return Response(status=204)


@app.route("/difference_hash")
def difference():
    img = capture_image()
    if img is None:
        return Response(status=204)

    similar_ids = get_most_similar(img, "difference", n=3)
    
    # Get card details for matches
    similar_cards = []
    for card_id in similar_ids:
        try:
            card = Card.find(card_id)
            similar_cards.append(card)
        except:
            continue
    
    if similar_cards:
        best_card = similar_cards[0]
        print_stats(best_card)
        
        return render_template("pokemon_card_matches.html", 
                             primary_card=best_card, 
                             all_matches=similar_cards)
    
    return Response(status=204)


@app.route("/wavelet_hash")
def wavelet():
    img = capture_image()
    if img is None:
        return Response(status=204)

    similar_ids = get_most_similar(img, "wavelet", n=3)
    
    # Get card details for matches
    similar_cards = []
    for card_id in similar_ids:
        try:
            card = Card.find(card_id)
            similar_cards.append(card)
        except:
            continue
    
    if similar_cards:
        best_card = similar_cards[0]
        print_stats(best_card)
        
        return render_template("pokemon_card_matches.html", 
                             primary_card=best_card, 
                             all_matches=similar_cards)
    
    return Response(status=204)


# Handling 404 errors


@app.errorhandler(404)
def not_found(e):
    """
    Error handler for not found (404) pages.
    """
    return render_template("404.html")


# Run the application if this script is executed
if __name__ == "__main__":
    app.run(debug=True)
