# Pokemon Card Scanner API

A powerful REST API for detecting and identifying Pokemon Trading Card Game cards using image hashing algorithms. Perfect for mobile app integration like TCGTrax!

## 🎯 Features

- **🔍 Card Detection**: Identify Pokemon cards from images using multiple hash algorithms
- **📱 Mobile Ready**: REST API with CORS support for mobile app integration
- **🎨 Multiple Algorithms**: Perceptual, Difference, and Wavelet hash for optimal accuracy
- **💰 Price Information**: Get current market prices from Cardmarket
- **📊 Confidence Scoring**: Know how accurate each detection is
- **🔍 Card Search**: Search the entire Pokemon TCG database
- **🌐 Easy Integration**: Simple JSON API with comprehensive documentation

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- pip

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/pokemon-card-scanner-api.git
cd pokemon-card-scanner-api
```

2. **Create virtual environment**
```bash
python -m venv venv
```

3. **Activate virtual environment**
```bash
# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

4. **Install dependencies**
```bash
pip install -r requirements.txt
```

5. **Start the API server**
```bash
python api_server.py
```

The API will be available at `http://localhost:5000`

## 📱 API Endpoints

### Health Check
```http
GET /api/health
```

### Scan Card Image
```http
POST /api/scan
Content-Type: multipart/form-data
```

**Parameters:**
- `image` (file, required): The card image to scan
- `hash_type` (string, optional): Hash algorithm (`perceptual`, `difference`, `wavelet`)
- `num_results` (integer, optional): Number of results (default: 5)

### Get Card Details
```http
GET /api/card/{card_id}
```

### Search Cards
```http
GET /api/search?q={query}&page={page}&page_size={page_size}
```

### Get Hash Types
```http
GET /api/hash-types
```

## 🔧 Hash Algorithms

### Perceptual Hash (phash)
- **Best for**: Overall similarity, lighting variations
- **Use when**: You have clear, well-lit photos

### Difference Hash (dhash)
- **Best for**: Edge detection, card structure
- **Use when**: Cards have distinct borders/patterns

### Wavelet Hash (whash)
- **Best for**: Pattern recognition, artwork details
- **Use when**: Cards have unique artwork/textures

## 📱 Mobile App Integration

### Expo/React Native Example

```javascript
// services/cardScanner.js
export class CardScannerService {
  constructor() {
    this.apiUrl = 'https://your-api-url.com/api';
  }

  async scanCard(imageUri, hashType = 'perceptual') {
    const formData = new FormData();
    formData.append('image', {
      uri: imageUri,
      type: 'image/jpeg',
      name: 'card.jpg'
    });
    formData.append('hash_type', hashType);

    const response = await fetch(`${this.apiUrl}/scan`, {
      method: 'POST',
      body: formData,
    });

    return await response.json();
  }
}
```

See [API_README.md](API_README.md) for complete integration examples.

## 🌐 Deployment

### Heroku
```bash
# Create Procfile
echo "web: python api_server.py" > Procfile

# Deploy
heroku create your-pokemon-scanner-api
git add .
git commit -m "Add Pokemon Card Scanner API"
git push heroku main
```

### Railway
```bash
# Install Railway CLI
npm install -g @railway/cli

# Deploy
railway login
railway init
railway up
```

### Docker
```bash
# Build and run
docker build -t pokemon-scanner-api .
docker run -p 5000:5000 pokemon-scanner-api
```

## 📊 API Response Example

```json
{
  "success": true,
  "hash_type_used": "perceptual",
  "num_results": 5,
  "primary_match": {
    "id": "sv3pt5-199",
    "name": "Charizard ex",
    "set": {
      "name": "Paldea Evolved",
      "series": "Scarlet & Violet"
    },
    "images": {
      "small": "https://images.pokemontcg.io/sv3pt5/199.png",
      "large": "https://images.pokemontcg.io/sv3pt5/199_hires.png"
    },
    "cardmarket": {
      "prices": {
        "averageSellPrice": 216.31
      }
    },
    "confidence": 0.85
  },
  "all_matches": [...],
  "scan_timestamp": "2025-07-10T21:30:04.123456"
}
```

## 🛠️ Development

### Project Structure
```
pokemon-card-scanner-api/
├── api_server.py          # Main API server
├── backend.py             # Original web app (for reference)
├── requirements.txt       # Python dependencies
├── API_README.md         # Detailed API documentation
├── templates/            # HTML templates (original app)
├── static/              # Static files (original app)
├── pokemontcgmanager/   # Pokemon TCG API wrapper
└── card_hashes_32b.pickle # Card hash database
```

### Running Tests
```bash
# Test the API endpoints
curl http://localhost:5000/api/health
```

### Contributing
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Pokemon TCG API](https://dev.pokemontcg.io/) for card data
- [ImageHash](https://github.com/JohannesBuchner/imagehash) for image hashing algorithms
- [OpenCV](https://opencv.org/) for image processing
- [Flask](https://flask.palletsprojects.com/) for the web framework

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/pokemon-card-scanner-api/issues)
- **Documentation**: [API_README.md](API_README.md)
- **Examples**: See the `examples/` directory

## 🚀 Roadmap

- [ ] Add authentication
- [ ] Implement caching
- [ ] Add rate limiting
- [ ] Support for other TCGs (Yu-Gi-Oh!, Magic: The Gathering)
- [ ] Real-time camera detection
- [ ] Batch processing
- [ ] Webhook support

---

**Made with ❤️ for the Pokemon TCG community**
