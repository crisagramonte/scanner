from flask import Flask, request, jsonify
from flask_cors import CORS
import cv2
import imagehash
from PIL import Image
import pandas as pd
import os
import io
from pokemontcgmanager.card import Card

app = Flask(__name__)
CORS(app)  # Enable CORS for mobile app integration

# Load the card hash database
card_hashes = pd.read_pickle("card_hashes_32b.pickle")

def preprocess_image(img: Image) -> Image:
    """
    Preprocess image for better hash comparison.
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

def get_most_similar(img: Image, hash_type="perceptual", n=5):
    """
    Find the most similar Pokémon card based on image hash.
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
        confidences = filtered_confidence.iloc[top_indices].tolist()
        return similar_ids, confidences
    else:
        best_index = sorted_indices[0]
        similar_id = filtered_hashes.iloc[best_index]["id"]
        confidence = filtered_confidence.iloc[best_index]
        return similar_id, confidence

def get_card_details(card_id):
    """
    Get detailed card information from Pokemon TCG API.
    """
    try:
        card = Card.find(card_id)
        return {
            'id': card.get('id'),
            'name': card.get('name'),
            'set': {
                'name': card.get('set', {}).get('name'),
                'series': card.get('set', {}).get('series'),
                'printedTotal': card.get('set', {}).get('printedTotal')
            },
            'number': card.get('number'),
            'images': card.get('images'),
            'cardmarket': card.get('cardmarket'),
            'tcgplayer': card.get('tcgplayer'),
            'rarity': card.get('rarity'),
            'types': card.get('types'),
            'attacks': card.get('attacks'),
            'weaknesses': card.get('weaknesses'),
            'resistances': card.get('resistances'),
            'retreatCost': card.get('retreatCost'),
            'convertedRetreatCost': card.get('convertedRetreatCost'),
            'hp': card.get('hp'),
            'supertype': card.get('supertype'),
            'subtypes': card.get('subtypes'),
            'level': card.get('level'),
            'evolvesFrom': card.get('evolvesFrom'),
            'evolvesTo': card.get('evolvesTo'),
            'rules': card.get('rules'),
            'abilities': card.get('abilities'),
            'flavorText': card.get('flavorText'),
            'nationalPokedexNumbers': card.get('nationalPokedexNumbers'),
            'legalities': card.get('legalities'),
            'regulationMark': card.get('regulationMark')
        }
    except Exception as e:
        return {'error': f'Failed to fetch card details: {str(e)}'}

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'message': 'Pokemon Card Scanner API is running',
        'version': '1.0.0'
    })

@app.route('/api/scan', methods=['POST'])
def scan_card():
    """
    Scan a Pokemon card image and return detection results.
    
    Expected request:
    - multipart/form-data with 'image' file
    - Optional 'hash_type' parameter (perceptual, difference, wavelet)
    - Optional 'num_results' parameter (default: 5)
    """
    try:
        # Check if image file is present
        if 'image' not in request.files:
            return jsonify({
                'error': 'No image file provided',
                'message': 'Please include an image file in the request'
            }), 400
        
        file = request.files['image']
        if file.filename == '':
            return jsonify({
                'error': 'No file selected',
                'message': 'Please select a valid image file'
            }), 400
        
        # Get parameters
        hash_type = request.form.get('hash_type', 'perceptual')
        num_results = int(request.form.get('num_results', 5))
        
        # Validate hash type
        valid_hash_types = ['perceptual', 'difference', 'wavelet']
        if hash_type not in valid_hash_types:
            return jsonify({
                'error': 'Invalid hash type',
                'message': f'Hash type must be one of: {", ".join(valid_hash_types)}'
            }), 400
        
        # Read and process image
        img_data = file.read()
        img = Image.open(io.BytesIO(img_data))
        
        # Get similar cards
        similar_ids, confidences = get_most_similar(img, hash_type, num_results)
        
        # Get detailed card information
        cards = []
        for i, card_id in enumerate(similar_ids):
            card_details = get_card_details(card_id)
            if 'error' not in card_details:
                card_details['confidence'] = confidences[i] if isinstance(confidences, list) else confidences
                cards.append(card_details)
        
        # Prepare response
        response = {
            'success': True,
            'hash_type_used': hash_type,
            'num_results': len(cards),
            'primary_match': cards[0] if cards else None,
            'all_matches': cards,
            'scan_timestamp': pd.Timestamp.now().isoformat()
        }
        
        return jsonify(response)
        
    except Exception as e:
        return jsonify({
            'error': 'Scan failed',
            'message': str(e),
            'success': False
        }), 500

@app.route('/api/card/<card_id>', methods=['GET'])
def get_card(card_id):
    """
    Get detailed information for a specific card by ID.
    """
    try:
        card_details = get_card_details(card_id)
        if 'error' in card_details:
            return jsonify(card_details), 404
        
        return jsonify({
            'success': True,
            'card': card_details
        })
        
    except Exception as e:
        return jsonify({
            'error': 'Failed to fetch card',
            'message': str(e),
            'success': False
        }), 500

@app.route('/api/search', methods=['GET'])
def search_cards():
    """
    Search for cards by name or other criteria.
    
    Query parameters:
    - q: search query
    - page: page number (default: 1)
    - page_size: results per page (default: 20)
    """
    try:
        query = request.args.get('q', '')
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 20))
        
        if not query:
            return jsonify({
                'error': 'No search query provided',
                'message': 'Please provide a search query parameter'
            }), 400
        
        # Search using Pokemon TCG API
        response = Card.where(q=query, pageSize=page_size, page=page)
        
        # Convert to list of card details
        cards = []
        for card in response:
            card_details = get_card_details(card.get('id'))
            if 'error' not in card_details:
                cards.append(card_details)
        
        return jsonify({
            'success': True,
            'query': query,
            'page': page,
            'page_size': page_size,
            'total_results': len(cards),
            'cards': cards
        })
        
    except Exception as e:
        return jsonify({
            'error': 'Search failed',
            'message': str(e),
            'success': False
        }), 500

@app.route('/api/hash-types', methods=['GET'])
def get_hash_types():
    """
    Get available hash types and their descriptions.
    """
    return jsonify({
        'success': True,
        'hash_types': {
            'perceptual': {
                'name': 'Perceptual Hash',
                'description': 'Analyzes overall visual structure and patterns. Best for overall similarity and lighting variations.',
                'best_for': 'Overall similarity, different lighting conditions'
            },
            'difference': {
                'name': 'Difference Hash',
                'description': 'Compares adjacent pixels to detect edges and contours. Best for card structure and borders.',
                'best_for': 'Edge detection, card structure, borders'
            },
            'wavelet': {
                'name': 'Wavelet Hash',
                'description': 'Uses wavelet transforms to analyze image at different scales. Best for pattern recognition.',
                'best_for': 'Pattern recognition, artwork details, textures'
            }
        }
    })

if __name__ == '__main__':
    # Run the API server
    print("🚀 Starting Pokemon Card Scanner API...")
    print("📱 Ready for mobile app integration!")
    print("🌐 API endpoints:")
    print("   - POST /api/scan - Scan a card image")
    print("   - GET  /api/card/<id> - Get card details")
    print("   - GET  /api/search - Search cards")
    print("   - GET  /api/health - Health check")
    print("   - GET  /api/hash-types - Available hash types")
    
    # Get port from environment variable (for Render deployment)
    port = int(os.environ.get('PORT', 5000))
    
    app.run(host='0.0.0.0', port=port, debug=False) 