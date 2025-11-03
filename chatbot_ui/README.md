# Sentinel Chatbot

A modern chatbot interface with JWT authentication, query history, and categorized example prompts that connects to your Sentinel API service.

## Features

✅ **JWT Token Authentication** - Secure login system with token persistence
✅ **Query History** - Automatically saves the last 20 queries with timestamps
✅ **Example Prompts** - Organized into 3 categories:
  - **SOP** - Standard Operating Procedures
  - **Events** - Event-related queries
  - **Tracking** - Status and progress tracking

✅ **Clean UI** - Modern, responsive design with Tailwind CSS
✅ **Real-time Chat** - Smooth messaging experience with loading indicators
✅ **Session Management** - Automatic token storage and session handling

## Files Included

1. **chatbot.jsx** - React component (for integration into existing React apps)
2. **chatbot.html** - Standalone HTML file (ready to use immediately)

## Quick Start (HTML Version)

### Prerequisites
- Your Sentinel API service running (default: `http://localhost:8000`)
- Valid user credentials for authentication

### Setup

1. **Update API URL** (if needed)
   Open `chatbot.html` and find this line:
   ```javascript
   const API_BASE_URL = 'http://localhost:8000'; // Update with your Sentinel API URL
   ```

2. **Open in Browser**
   Simply open `chatbot.html` in any modern web browser (Chrome, Firefox, Safari, Edge)

3. **Login**
   - Enter your username and password
   - Click "Sign In"

That's it! The chatbot is ready to use.

## API Integration

The chatbot expects your Sentinel API to have these endpoints:

### 1. Login Endpoint
```
POST /auth/login
Content-Type: application/json

Request Body:
{
  "username": "string",
  "password": "string"
}

Response:
{
  "access_token": "string"
}
```

### 2. Chat Endpoint
```
POST /api/chat
Content-Type: application/json
Authorization: Bearer {token}

Request Body:
{
  "message": "string"
}

Response:
{
  "response": "string"
  // OR
  "message": "string"
}
```

## Using the React Component

If you want to integrate the chatbot into an existing React application:

### Installation

1. Copy `chatbot.jsx` to your React project
2. Install dependencies:
   ```bash
   npm install lucide-react
   ```

3. Import and use:
   ```jsx
   import SentinelChatbot from './chatbot';

   function App() {
     return <SentinelChatbot />;
   }
   ```

### Requirements
- React 18+
- Tailwind CSS configured in your project
- lucide-react for icons

## Customization

### Change Example Prompts

Edit the `EXAMPLE_PROMPTS` object in the code:

```javascript
const EXAMPLE_PROMPTS = {
  sop: [
    "Your custom SOP prompt 1",
    "Your custom SOP prompt 2",
    // Add more...
  ],
  events: [
    "Your custom events prompt 1",
    // Add more...
  ],
  tracking: [
    "Your custom tracking prompt 1",
    // Add more...
  ]
};
```

### Add More Categories

Simply add a new key to the `EXAMPLE_PROMPTS` object:

```javascript
const EXAMPLE_PROMPTS = {
  sop: [...],
  events: [...],
  tracking: [...],
  reports: [  // New category
    "Generate monthly report",
    "Show quarterly statistics"
  ]
};
```

### Change History Limit

Find this line and change `20` to your desired number:

```javascript
].slice(0, 20); // Keep only last 20
```

### Customize Colors

The chatbot uses Tailwind CSS classes. Key color classes to change:

- Primary color: `bg-indigo-600`, `text-indigo-600`, etc.
- Change all `indigo` to another Tailwind color like `blue`, `purple`, `green`, etc.

## Features Explained

### Authentication
- JWT token is stored in `localStorage`
- Automatic session persistence (survives page refresh)
- Auto-logout on token expiration (401 errors)
- Secure logout clears all stored data

### Query History
- Stores last 20 queries automatically
- Includes query text, response preview, and timestamp
- Persisted in `localStorage`
- Click any history item to reuse the query

### Example Prompts
- 3 categories with 4 examples each
- Click any example to populate the input field
- Easy to customize and extend
- Helps users discover chatbot capabilities

### Message Interface
- Real-time message display
- Timestamps for all messages
- Loading indicator during API calls
- Error handling with clear error messages
- Auto-scroll to latest message

## Troubleshooting

### "Failed to get response" Error
- Check that your Sentinel API is running
- Verify the API_BASE_URL is correct
- Check browser console for CORS errors
- Ensure your API endpoints match the expected format

### "Invalid credentials" Error
- Verify username and password are correct
- Check that `/auth/login` endpoint is working
- Ensure API returns `access_token` in response

### "Session expired" Error
- JWT token has expired
- Simply log in again
- Consider implementing token refresh in your API

### CORS Issues
Your Sentinel API needs to allow CORS. Add these headers:
```python
# FastAPI example
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Or specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Browser Support

- ✅ Chrome 90+
- ✅ Firefox 88+
- ✅ Safari 14+
- ✅ Edge 90+

## Data Storage

The chatbot stores data in browser `localStorage`:
- `sentinel_token` - JWT authentication token
- `query_history` - Last 20 queries with metadata

To clear stored data:
1. Logout (clears token and messages)
2. Or manually: Open browser DevTools > Application > Local Storage > Clear

## Security Notes

- JWT token stored in localStorage (consider httpOnly cookies for production)
- Passwords never stored
- All API calls use Authorization header
- Token automatically removed on logout
- Session expires on 401 response

## Future Enhancements

Consider adding:
- [ ] Token refresh mechanism
- [ ] Message markdown rendering
- [ ] File upload support
- [ ] Voice input
- [ ] Export chat history
- [ ] Dark mode
- [ ] Multi-language support
- [ ] Typing indicators
- [ ] Message reactions

## License

This chatbot interface is provided as-is for use with your Sentinel API service.

## Support

For issues related to:
- **Chatbot UI**: Check this README and browser console
- **API Connection**: Verify your Sentinel API is running correctly
- **Authentication**: Ensure your JWT implementation matches expected format
