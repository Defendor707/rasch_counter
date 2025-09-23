# Rasch Counter Mobile App

React Native mobile application for Rasch model-based test analysis.

## Features

- 📱 **Cross-platform**: Works on both iOS and Android
- 📊 **File Upload**: Upload Excel files directly from device
- 🔄 **Real-time Progress**: Live progress tracking during analysis
- 📈 **Results Display**: Interactive charts and statistics
- 📄 **Export**: Download Excel and PDF reports
- 🎨 **Modern UI**: Beautiful gradient design with animations

## Prerequisites

- Node.js (v16 or higher)
- React Native CLI
- Android Studio (for Android development)
- Xcode (for iOS development, macOS only)

## Installation

1. Install dependencies:
```bash
npm install
```

2. For iOS (macOS only):
```bash
cd ios && pod install && cd ..
```

3. Start Metro bundler:
```bash
npm start
```

4. Run on device/emulator:

**Android:**
```bash
npm run android
```

**iOS:**
```bash
npm run ios
```

## Configuration

Update the `API_BASE_URL` in `App.tsx` to point to your web server:

```typescript
const API_BASE_URL = 'http://your-server-ip:5000';
```

## Usage

1. **Upload File**: Tap "Excel fayl tanlash" to select an Excel file
2. **Monitor Progress**: Watch real-time progress during analysis
3. **View Results**: See comprehensive statistics and grade distribution
4. **Download Reports**: Get Excel or PDF reports

## Architecture

- **Frontend**: React Native with TypeScript
- **Backend**: Flask web API (shared with web app)
- **File Handling**: React Native Document Picker
- **UI Components**: Custom components with LinearGradient
- **State Management**: React hooks (useState)

## API Integration

The mobile app communicates with the Flask web API:

- `POST /upload` - Upload Excel file
- `GET /status/{session_id}` - Get processing status
- `GET /results/{session_id}` - Get analysis results
- `GET /download/{session_id}/{type}` - Download reports
- `GET /api/sample` - Generate sample data

## Development

### Project Structure
```
mobile_app/
├── App.tsx              # Main application component
├── package.json         # Dependencies and scripts
├── README.md           # This file
└── android/            # Android-specific files
└── ios/               # iOS-specific files
```

### Key Components

- **File Upload**: Document picker integration
- **Progress Tracking**: Real-time status updates
- **Results Display**: Dynamic data visualization
- **Download System**: File export functionality

## Troubleshooting

### Common Issues

1. **Metro bundler issues**: Clear cache with `npx react-native start --reset-cache`
2. **Android build issues**: Clean project with `cd android && ./gradlew clean`
3. **iOS build issues**: Clean with `cd ios && xcodebuild clean`

### Network Configuration

For testing on physical devices, ensure:
- Device and server are on same network
- Firewall allows connections on port 5000
- Update `API_BASE_URL` with correct IP address

## Contributing

1. Follow React Native best practices
2. Use TypeScript for type safety
3. Test on both iOS and Android
4. Maintain responsive design

## License

Same as main Rasch Counter project.
