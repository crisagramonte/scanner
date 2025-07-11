# Pokemon Card Scanner API

A REST API that wraps the PokeCard-TCG-detector functionality for easy integration with mobile apps like TCGTrax.

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Start the API Server
```bash
python api_server.py
```

The API will be available at `http://localhost:5000`

## 📱 API Endpoints

### Health Check
```http
GET /api/health
```
**Response:**
```json
{
  "status": "healthy",
  "message": "Pokemon Card Scanner API is running",
  "version": "1.0.0"
}
```

### Scan Card Image
```http
POST /api/scan
Content-Type: multipart/form-data
```

**Parameters:**
- `image` (file, required): The card image to scan
- `hash_type` (string, optional): Hash algorithm to use (`perceptual`, `difference`, `wavelet`)
- `num_results` (integer, optional): Number of results to return (default: 5)

**Example Request:**
```javascript
const formData = new FormData();
formData.append('image', imageFile);
formData.append('hash_type', 'perceptual');
formData.append('num_results', '5');

fetch('http://localhost:5000/api/scan', {
  method: 'POST',
  body: formData
});
```

**Response:**
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
      "series": "Scarlet & Violet",
      "printedTotal": 193
    },
    "number": "199",
    "images": {
      "small": "https://images.pokemontcg.io/sv3pt5/199.png",
      "large": "https://images.pokemontcg.io/sv3pt5/199_hires.png"
    },
    "cardmarket": {
      "prices": {
        "averageSellPrice": 216.31
      },
      "updatedAt": "2025-07-10"
    },
    "confidence": 0.85
  },
  "all_matches": [...],
  "scan_timestamp": "2025-07-10T21:30:04.123456"
}
```

### Get Card Details
```http
GET /api/card/{card_id}
```

**Example:**
```http
GET /api/card/sv3pt5-199
```

### Search Cards
```http
GET /api/search?q={query}&page={page}&page_size={page_size}
```

**Parameters:**
- `q` (string, required): Search query
- `page` (integer, optional): Page number (default: 1)
- `page_size` (integer, optional): Results per page (default: 20)

**Example:**
```http
GET /api/search?q=name:Charizard&page=1&page_size=10
```

### Get Hash Types
```http
GET /api/hash-types
```

**Response:**
```json
{
  "success": true,
  "hash_types": {
    "perceptual": {
      "name": "Perceptual Hash",
      "description": "Analyzes overall visual structure and patterns. Best for overall similarity and lighting variations.",
      "best_for": "Overall similarity, different lighting conditions"
    },
    "difference": {
      "name": "Difference Hash",
      "description": "Compares adjacent pixels to detect edges and contours. Best for card structure and borders.",
      "best_for": "Edge detection, card structure, borders"
    },
    "wavelet": {
      "name": "Wavelet Hash",
      "description": "Uses wavelet transforms to analyze image at different scales. Best for pattern recognition.",
      "best_for": "Pattern recognition, artwork details, textures"
    }
  }
}
```

## 📱 Expo Integration Example

### 1. Create Card Scanner Service
```javascript
// services/cardScanner.js
export class CardScannerService {
  constructor() {
    this.apiUrl = 'http://localhost:5000/api'; // Change to your deployed URL
  }

  async scanCard(imageUri, hashType = 'perceptual', numResults = 5) {
    try {
      const formData = new FormData();
      formData.append('image', {
        uri: imageUri,
        type: 'image/jpeg',
        name: 'card.jpg'
      });
      formData.append('hash_type', hashType);
      formData.append('num_results', numResults.toString());

      const response = await fetch(`${this.apiUrl}/scan`, {
        method: 'POST',
        body: formData,
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      const result = await response.json();
      
      if (!result.success) {
        throw new Error(result.message || 'Scan failed');
      }

      return result;
    } catch (error) {
      console.error('Card scanning failed:', error);
      throw error;
    }
  }

  async searchCards(query, page = 1, pageSize = 20) {
    try {
      const response = await fetch(
        `${this.apiUrl}/search?q=${encodeURIComponent(query)}&page=${page}&page_size=${pageSize}`
      );
      
      const result = await response.json();
      
      if (!result.success) {
        throw new Error(result.message || 'Search failed');
      }

      return result;
    } catch (error) {
      console.error('Card search failed:', error);
      throw error;
    }
  }

  async getCardDetails(cardId) {
    try {
      const response = await fetch(`${this.apiUrl}/card/${cardId}`);
      const result = await response.json();
      
      if (!result.success) {
        throw new Error(result.message || 'Failed to fetch card details');
      }

      return result.card;
    } catch (error) {
      console.error('Failed to get card details:', error);
      throw error;
    }
  }

  async getHashTypes() {
    try {
      const response = await fetch(`${this.apiUrl}/hash-types`);
      const result = await response.json();
      return result.hash_types;
    } catch (error) {
      console.error('Failed to get hash types:', error);
      throw error;
    }
  }
}
```

### 2. Create Scanner Component
```jsx
// components/CardScanner.js
import React, { useState } from 'react';
import { View, Text, TouchableOpacity, Image, Alert, ActivityIndicator } from 'react-native';
import * as ImagePicker from 'expo-image-picker';
import { CardScannerService } from '../services/cardScanner';

export default function CardScanner({ onCardDetected }) {
  const [scanning, setScanning] = useState(false);
  const [result, setResult] = useState(null);
  const scanner = new CardScannerService();

  const handleScan = async (scanMethod) => {
    setScanning(true);
    try {
      let imageUri;
      
      if (scanMethod === 'camera') {
        const { status } = await ImagePicker.requestCameraPermissionsAsync();
        if (status !== 'granted') {
          Alert.alert('Permission Denied', 'Camera permission is required');
          return;
        }

        const result = await ImagePicker.launchCameraAsync({
          mediaTypes: ImagePicker.MediaTypeOptions.Images,
          allowsEditing: true,
          aspect: [600, 825], // Pokemon card aspect ratio
          quality: 0.8,
        });

        if (result.canceled) return;
        imageUri = result.assets[0].uri;
      } else {
        const result = await ImagePicker.launchImageLibraryAsync({
          mediaTypes: ImagePicker.MediaTypeOptions.Images,
          allowsEditing: true,
          aspect: [600, 825],
          quality: 0.8,
        });

        if (result.canceled) return;
        imageUri = result.assets[0].uri;
      }

      const scanResult = await scanner.scanCard(imageUri);
      setResult(scanResult);
      onCardDetected(scanResult);
      
    } catch (error) {
      Alert.alert('Scan Failed', error.message);
    } finally {
      setScanning(false);
    }
  };

  return (
    <View style={{ padding: 20 }}>
      <Text style={{ fontSize: 24, fontWeight: 'bold', marginBottom: 20 }}>
        Scan Pokemon Card
      </Text>
      
      <TouchableOpacity 
        style={{ 
          backgroundColor: '#007AFF', 
          padding: 15, 
          borderRadius: 8, 
          marginBottom: 10 
        }}
        onPress={() => handleScan('camera')}
        disabled={scanning}
      >
        <Text style={{ color: 'white', textAlign: 'center', fontSize: 16 }}>
          {scanning ? 'Scanning...' : '📷 Scan with Camera'}
        </Text>
      </TouchableOpacity>

      <TouchableOpacity 
        style={{ 
          backgroundColor: '#34C759', 
          padding: 15, 
          borderRadius: 8 
        }}
        onPress={() => handleScan('gallery')}
        disabled={scanning}
      >
        <Text style={{ color: 'white', textAlign: 'center', fontSize: 16 }}>
          {scanning ? 'Scanning...' : '🖼️ Choose from Gallery'}
        </Text>
      </TouchableOpacity>

      {scanning && (
        <View style={{ marginTop: 20, alignItems: 'center' }}>
          <ActivityIndicator size="large" color="#007AFF" />
          <Text style={{ marginTop: 10 }}>Analyzing card...</Text>
        </View>
      )}

      {result && (
        <View style={{ marginTop: 20, padding: 15, backgroundColor: '#f0f0f0', borderRadius: 8 }}>
          <Text style={{ fontSize: 18, fontWeight: 'bold' }}>
            Detected: {result.primary_match?.name}
          </Text>
          <Text style={{ fontSize: 14, color: '#666' }}>
            Set: {result.primary_match?.set?.name}
          </Text>
          <Text style={{ fontSize: 14, color: '#666' }}>
            Confidence: {(result.primary_match?.confidence * 100).toFixed(1)}%
          </Text>
          {result.primary_match?.cardmarket?.prices?.averageSellPrice && (
            <Text style={{ fontSize: 14, color: '#666' }}>
              Price: ${result.primary_match.cardmarket.prices.averageSellPrice}
            </Text>
          )}
        </View>
      )}
    </View>
  );
}
```

### 3. Use in Your App
```jsx
// App.js or your main screen
import React, { useState } from 'react';
import { View, Text } from 'react-native';
import CardScanner from './components/CardScanner';

export default function App() {
  const [detectedCard, setDetectedCard] = useState(null);

  const handleCardDetected = (result) => {
    setDetectedCard(result.primary_match);
    // Add to your collection, show details, etc.
    console.log('Card detected:', result.primary_match);
  };

  return (
    <View style={{ flex: 1, padding: 20 }}>
      <Text style={{ fontSize: 28, fontWeight: 'bold', marginBottom: 20 }}>
        TCGTrax Card Scanner
      </Text>
      
      <CardScanner onCardDetected={handleCardDetected} />
      
      {detectedCard && (
        <View style={{ marginTop: 20 }}>
          <Text style={{ fontSize: 20, fontWeight: 'bold' }}>
            Last Scanned: {detectedCard.name}
          </Text>
        </View>
      )}
    </View>
  );
}
```

## 🌐 Deployment Options

### 1. Local Development
```bash
python api_server.py
```

### 2. Heroku Deployment
```bash
# Create Procfile
echo "web: python api_server.py" > Procfile

# Deploy to Heroku
heroku create your-pokemon-scanner-api
git add .
git commit -m "Add Pokemon Card Scanner API"
git push heroku main
```

### 3. Railway Deployment
```bash
# Install Railway CLI
npm install -g @railway/cli

# Deploy
railway login
railway init
railway up
```

### 4. Docker Deployment
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 5000

CMD ["python", "api_server.py"]
```

## 🔧 Configuration

### Environment Variables
- `PORT`: Server port (default: 5000)
- `HOST`: Server host (default: 0.0.0.0)
- `DEBUG`: Debug mode (default: True)

### CORS Configuration
The API includes CORS support for mobile app integration. You can customize CORS settings in `api_server.py`:

```python
from flask_cors import CORS

# Allow all origins (for development)
CORS(app)

# Or configure specific origins
CORS(app, origins=['http://localhost:3000', 'https://yourapp.com'])
```

## 📊 API Response Format

All API responses follow this format:

**Success Response:**
```json
{
  "success": true,
  "data": {...},
  "message": "Optional message"
}
```

**Error Response:**
```json
{
  "success": false,
  "error": "Error type",
  "message": "Error description"
}
```

## 🚀 Next Steps

1. **Deploy the API** to a cloud service (Heroku, Railway, AWS, etc.)
2. **Update the API URL** in your Expo app's `CardScannerService`
3. **Add error handling** and retry logic
4. **Implement caching** for frequently accessed cards
5. **Add authentication** if needed
6. **Monitor API usage** and performance

## 📞 Support

For issues or questions:
1. Check the API health endpoint: `GET /api/health`
2. Review the error messages in the response
3. Ensure all required files (`card_hashes_32b.pickle`) are present
4. Verify network connectivity and CORS settings 