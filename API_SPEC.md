# API Specification – Short5 Platform

## Base URL
- **Development:** `${BACKEND_BASE_URL}/api/v1` (default: `http://localhost:8000/api/v1`)
  - Configure via `BACKEND_BASE_URL` in `.env`
- **Production:** Set `BACKEND_BASE_URL` to your production URL

## Authentication
All authenticated endpoints require a JWT token in the Authorization header:
```
Authorization: Bearer <token>
```

## Error Response Format
```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": {}
  }
}
```

### Error Codes
- `VALIDATION_ERROR` - Request validation failed
- `UNAUTHORIZED` - Missing or invalid authentication
- `FORBIDDEN` - Insufficient permissions
- `NOT_FOUND` - Resource not found
- `CONFLICT` - Resource conflict (e.g., duplicate email)
- `RATE_LIMIT_EXCEEDED` - Too many requests
- `INTERNAL_ERROR` - Server error

---

## Authentication Endpoints

### POST `/auth/register`
Register a new user.

**Request:**
```json
{
  "username": "string (3-30 chars, alphanumeric + _)",
  "email": "string (valid email)",
  "password": "string (min 8 chars)"
}
```

**Response:** `201 Created`
```json
{
  "user": {
    "id": "uuid",
    "username": "string",
    "email": "string",
    "created_at": "2024-01-01T00:00:00Z"
  },
  "access_token": "jwt_token",
  "refresh_token": "jwt_token"
}
```

**Errors:**
- `400` - Validation error
- `409` - Username or email already exists

---

### POST `/auth/login`
Login with email/username and password.

**Request:**
```json
{
  "email": "string",
  "password": "string"
}
```

**Response:** `200 OK`
```json
{
  "user": {
    "id": "uuid",
    "username": "string",
    "email": "string"
  },
  "access_token": "jwt_token",
  "refresh_token": "jwt_token"
}
```

**Errors:**
- `401` - Invalid credentials

---

### POST `/auth/refresh`
Refresh access token using refresh token.

**Request:**
```json
{
  "refresh_token": "string"
}
```

**Response:** `200 OK`
```json
{
  "access_token": "jwt_token",
  "refresh_token": "jwt_token"
}
```

---

### POST `/auth/logout`
Logout (invalidate refresh token).

**Request:**
```json
{
  "refresh_token": "string"
}
```

**Response:** `200 OK`
```json
{
  "message": "Logged out successfully"
}
```

---

## User Endpoints

### GET `/users/me`
Get current user profile.

**Response:** `200 OK`
```json
{
  "id": "uuid",
  "username": "string",
  "email": "string",
  "created_at": "2024-01-01T00:00:00Z",
  "stats": {
    "videos_uploaded": 10,
    "total_likes_received": 150,
    "total_views": 5000
  }
}
```

---

### GET `/users/{user_id}`
Get public user profile.

**Response:** `200 OK`
```json
{
  "id": "uuid",
  "username": "string",
  "created_at": "2024-01-01T00:00:00Z",
  "stats": {
    "videos_uploaded": 10,
    "total_likes_received": 150,
    "total_views": 5000
  }
}
```

---

### GET `/users/me/liked`
Get user's liked videos (saved list).

**Query Parameters:**
- `cursor` (optional) - Pagination cursor
- `limit` (optional, default: 20, max: 100) - Number of results

**Response:** `200 OK`
```json
{
  "videos": [
    {
      "id": "uuid",
      "title": "string",
      "description": "string",
      "thumbnail": "url",
      "url_mp4": "url",
      "user": {
        "id": "uuid",
        "username": "string"
      },
      "stats": {
        "likes": 10,
        "views": 100
      },
      "created_at": "2024-01-01T00:00:00Z"
    }
  ],
  "next_cursor": "string|null",
  "has_more": true
}
```

---

## Video Endpoints

### POST `/videos/upload`
Upload a video file (multipart/form-data).

**Request:**
- `file` (file) - Video file (max 500MB, formats: mp4, mov, avi)
- `title` (string, optional) - Video title
- `description` (string, optional) - Video description

**Response:** `202 Accepted`
```json
{
  "video_id": "uuid",
  "status": "processing",
  "message": "Video upload accepted, processing started"
}
```

**Errors:**
- `400` - Invalid file format or size
- `413` - File too large

---

### GET `/videos/{video_id}`
Get video details.

**Response:** `200 OK`
```json
{
  "id": "uuid",
  "title": "string",
  "description": "string",
  "status": "ready|processing|failed",
  "thumbnail": "url",
  "url_mp4": "url|null",
  "user": {
    "id": "uuid",
    "username": "string"
  },
  "stats": {
    "likes": 10,
    "not_likes": 5,
    "views": 100
  },
  "created_at": "2024-01-01T00:00:00Z"
}
```

**Errors:**
- `404` - Video not found

---

### POST `/videos/{video_id}/vote`
Swipe/vote on a video (Like or Not-Like).

**Request:**
```json
{
  "direction": "like|not_like"
}
```

**Response:** `200 OK`
```json
{
  "message": "Vote recorded",
  "video_id": "uuid",
  "direction": "like|not_like"
}
```

**Errors:**
- `400` - Invalid direction
- `404` - Video not found
- `409` - Already voted on this video

---

### DELETE `/videos/{video_id}`
Delete own video.

**Response:** `200 OK`
```json
{
  "message": "Video deleted successfully"
}
```

**Errors:**
- `403` - Not video owner
- `404` - Video not found

---

### POST `/videos/{video_id}/view`
Record video view/watch time.

**Request:**
```json
{
  "watched_seconds": 30
}
```

**Response:** `200 OK`
```json
{
  "message": "View recorded"
}
```

---

## Feed Endpoints

### GET `/feed`
Get personalized video feed (cursor-based pagination).

**Query Parameters:**
- `cursor` (optional) - Pagination cursor
- `limit` (optional, default: 10, max: 50) - Number of videos

**Response:** `200 OK`
```json
{
  "videos": [
    {
      "id": "uuid",
      "title": "string",
      "description": "string",
      "thumbnail": "url",
      "url_mp4": "url",
      "user": {
        "id": "uuid",
        "username": "string"
      },
      "stats": {
        "likes": 10,
        "views": 100
      },
      "created_at": "2024-01-01T00:00:00Z"
    }
  ],
  "next_cursor": "string|null",
  "has_more": true
}
```

**Algorithm:**
- Prioritizes videos based on user's like history
- Reduces videos similar to not-liked content
- Falls back to popular/recent videos for new users

---

## Admin Endpoints

### GET `/admin/videos/pending`
Get videos pending moderation (admin only).

**Query Parameters:**
- `cursor` (optional)
- `limit` (optional, default: 20)

**Response:** `200 OK`
```json
{
  "videos": [
    {
      "id": "uuid",
      "title": "string",
      "user": {
        "id": "uuid",
        "username": "string"
      },
      "status": "processing",
      "created_at": "2024-01-01T00:00:00Z"
    }
  ],
  "next_cursor": "string|null"
}
```

---

### POST `/admin/videos/{video_id}/approve`
Approve a video (admin only).

**Response:** `200 OK`
```json
{
  "message": "Video approved",
  "video_id": "uuid"
}
```

---

### POST `/admin/videos/{video_id}/reject`
Reject a video (admin only).

**Request:**
```json
{
  "reason": "string (optional)"
}
```

**Response:** `200 OK`
```json
{
  "message": "Video rejected",
  "video_id": "uuid"
}
```

---

### GET `/admin/reports`
Get all reports (admin only).

**Query Parameters:**
- `status` (optional) - `pending|resolved|dismissed`
- `cursor` (optional)
- `limit` (optional, default: 20)

**Response:** `200 OK`
```json
{
  "reports": [
    {
      "id": "uuid",
      "type": "video|user",
      "target_id": "uuid",
      "reason": "string",
      "status": "pending",
      "created_at": "2024-01-01T00:00:00Z"
    }
  ],
  "next_cursor": "string|null"
}
```

---

## Rate Limiting
- **Public endpoints:** 100 requests/minute
- **Authenticated endpoints:** 1000 requests/minute
- **Upload endpoints:** 10 requests/minute
- **Admin endpoints:** 5000 requests/minute

---

## WebSocket (Future)
Real-time updates for video processing status:
- `ws://localhost:8000/ws/video/{video_id}`
- Events: `processing`, `ready`, `failed`

