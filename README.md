Here's a professional English description of the Flask video sharing application in Markdown format:

```markdown
# Video Sharing Platform with Flask

## Overview
A full-featured video sharing web application built with Python Flask that supports user registration, video uploading, real-time interactions, and social features. The platform includes comprehensive media handling capabilities with automatic thumbnail generation and video processing.

## Key Features

### User Management
- Secure registration/login with password hashing
- User profiles with follower counts
- Session-based authentication
- Follow/unfollow other users

### Video Handling
- MP4/WebM/MKV uploads (500MB max)
- Automatic thumbnail generation using FFmpeg
- Video duration calculation
- Unique filename handling to prevent conflicts
- Database storage of video metadata (JSON)
- Manual database update endpoint (`/update`)

### Interactive Features
- Real-time danmu (commenting overlay) with SSE streaming
- Like/dislike videos
- Favorite/unfavorite videos
- Video comments system
- View counters

### Social Features
- User following system
- Favorites collection
- User profile pages showing uploaded videos
- Author attribution for videos

### Content Discovery
- Search functionality
- Homepage video listing
- Favorites page for logged-in users
- Video recommendations

## Technical Stack
- **Core Framework**: Flask
- **Security**: Werkzeug (password hashing, file security)
- **Media Processing**: FFmpeg (video thumbnails, duration)
- **Data Storage**: JSON files (videos.json, users.json)
- **Real-time Updates**: Server-Sent Events (SSE)
- **Frontend**: HTML templates with dynamic rendering
- **Deployment**: HTTPS with SSL/TLS encryption

## Configuration
```python
app.config.update({
    'UPLOAD_FOLDER': 'static/videos',
    'THUMBNAIL_FOLDER': 'static/thumbnails',
    'DATA_FILE': 'videos.json',
    'MAX_CONTENT_LENGTH': 500 * 1024 * 1024,  # 500MB
    'ALLOWED_EXTENSIONS': {'mp4', 'webm', 'mkv'},
    'SECRET_KEY': 'your_secret_key_here',
    'USERS_FILE': 'users.json',
    'SERVER_NAME': 'www.yourdomain.com:5062'
})
```

## Security Measures
- Secure filename handling
- Password hashing with Werkzeug
- Login-required decorators for protected routes
- Proxy-aware request handling
- SSL/TLS encryption
- File permission management (chmod 644)

## Running the Application
1. Install requirements: `Flask, Werkzeug`
2. Ensure FFmpeg is installed system-wide
3. Place SSL certificates in project root:
   - `cert.pem`
   - `key.pem`
4. Run:
```bash
python app.py
```
5. Access at: `https://www.yourdomain.com:5062`

## Endpoints
- `/` - Homepage with video listings
- `/search` - Video search
- `/upload` - Video upload page
- `/video/<vid>` - Video player page
- `/register`/`/login` - User authentication
- `/favorites` - User's favorite videos
- `/user/<username>` - User profile
- `/video/<vid>/danmu` - Danmu submission
- `/video/<vid>/danmu_stream` - SSE danmu stream
- `/follow/<username>` - Follow/unfollow users
- `/video/<vid>/(like|favorite)` - Engagement actions

## File Structure
```
├── app.py                 # Main application
├── cert.pem               # SSL certificate
├── key.pem                # SSL private key
├── static/
│   ├── videos/            # Uploaded videos
│   └── thumbnails/        # Generated thumbnails
├── templates/             # Flask HTML templates
├── users.json             # User database
└── videos.json            # Video metadata database
```

## Notes
- Uses FFmpeg for video processing (ensure it's in system PATH)
- Default thumbnails used if generation fails
- Tested with Python 3.7+
- Includes database initialization for first-time setup
- Session-based user tracking
- Responsive design with dynamic video player sizing
```

This description covers the application's functionality, technical implementation, security features, and operational requirements in a professional format suitable for documentation or project presentation.
