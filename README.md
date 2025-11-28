# Short-Video Platform

A self-hosted, mobile-first short-video platform similar to TikTok, built with Nuxt 4 and FastAPI.

## Features

- 🎥 **Video Feed** - Vertical swipe feed with infinite scroll
- 👆 **Swipe Mechanics** - Tinder-like swipe: Right = Like, Left = Not-Like
- 📱 **Mobile-First PWA** - Progressive Web App optimized for mobile devices
- 🎬 **Video Processing** - Automatic transcoding to HLS with multiple quality levels
- 🔐 **Authentication** - JWT-based user authentication
- 🎯 **Personalized Feed** - Recommendation algorithm based on user interactions
- 📊 **Admin Dashboard** - Content moderation and reporting system

## Tech Stack

### Frontend
- **Nuxt 4** - Vue.js framework with SSR/SSG
- **TypeScript** - Type-safe development
- **Tailwind CSS 4** - Utility-first CSS framework
- **Nuxt UI** - Component library
- **Pinia** - State management

### Backend
- **FastAPI** - Modern Python web framework
- **PostgreSQL** - Relational database
- **SQLAlchemy** - ORM
- **Redis** - Caching and message broker
- **Celery** - Background job processing

### Video Processing
- **FFmpeg** - Video transcoding
- **HLS** - HTTP Live Streaming
- **Docker** - Containerized worker

### Infrastructure
- **Docker Compose** - Local development environment
- **AWS S3 / Cloudflare R2** - Object storage
- **Nginx** (optional) - Reverse proxy

## Project Structure

```
.
├── backend/              # FastAPI backend
│   ├── app/
│   │   ├── api/         # API routes
│   │   ├── core/        # Core utilities (config, security, database)
│   │   ├── models/      # Database models
│   │   └── tasks/       # Celery tasks
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/            # Nuxt 4 frontend
│   ├── components/      # Vue components
│   ├── pages/           # Nuxt pages
│   ├── stores/          # Pinia stores
│   ├── composables/     # Composables
│   └── package.json
├── video_worker/        # FFmpeg video processing worker
│   ├── worker.py
│   └── Dockerfile
├── database/            # Database schema and migrations
│   ├── schema.sql
│   └── migrations/
├── docker-compose.yml   # Docker Compose configuration
├── .env.example         # Environment variables template
├── API_SPEC.md          # API specification
├── RECOMMENDATION_ALGORITHM.md  # Feed algorithm documentation
├── RFC.md               # Request for Comments
└── PRD.md               # Product Requirements Document
```

## Getting Started

### Prerequisites

- Docker and Docker Compose
- Node.js 20+ (for local frontend development)
- Python 3.11+ (for local backend development)
- PostgreSQL 15+ (if not using Docker)
- Redis 7+ (if not using Docker)

### Quick Start with Docker

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd short5_swiper_bugagaa
   ```

2. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Start all services**
   ```bash
   docker-compose up -d
   ```

4. **Initialize database**
   ```bash
   docker-compose exec postgres psql -U short5_user -d short5_db -f /docker-entrypoint-initdb.d/01-schema.sql
   ```

5. **Access the application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

### Local Development

#### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Set environment variables
export DATABASE_URL="postgresql://user:password@localhost:5432/short5_db"
export REDIS_URL="redis://localhost:6379/0"
export JWT_SECRET_KEY="your-secret-key"

# Run migrations (using Alembic)
alembic upgrade head

# Start server
uvicorn app.main:app --reload
```

#### Frontend

```bash
cd frontend
npm install

# Set environment variables
export NUXT_PUBLIC_API_BASE_URL="http://localhost:8000/api/v1"

# Start development server
npm run dev
```

#### Video Worker

```bash
cd video_worker
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Set environment variables
export DATABASE_URL="postgresql://user:password@localhost:5432/short5_db"
export REDIS_URL="redis://localhost:6379/0"
export AWS_ACCESS_KEY_ID="your-key"
export AWS_SECRET_ACCESS_KEY="your-secret"
export S3_BUCKET_NAME="your-bucket"

# Start Celery worker
celery -A worker worker --loglevel=info
```

## Configuration

### Environment Variables

See `.env.example` for all available configuration options.

Key variables:
- `DATABASE_URL` - PostgreSQL connection string
- `REDIS_URL` - Redis connection string
- `JWT_SECRET_KEY` - Secret key for JWT tokens
- `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` - S3/R2 credentials
- `S3_BUCKET_NAME` - S3 bucket name
- `S3_ENDPOINT_URL` - Cloudflare R2 endpoint (if using R2)

### Video Processing Settings

Video encoding profiles are configured in `video_worker/worker.py`:
- **720p**: 1280x720, 2500k bitrate
- **480p**: 854x480, 1000k bitrate

HLS segment duration: 10 seconds

## API Documentation

See [API_SPEC.md](./API_SPEC.md) for complete API documentation.

### Key Endpoints

- `POST /api/v1/auth/register` - User registration
- `POST /api/v1/auth/login` - User login
- `GET /api/v1/feed` - Get personalized video feed
- `POST /api/v1/videos/upload` - Upload video
- `POST /api/v1/videos/{id}/vote` - Swipe/vote on video

## Database Schema

See [database/schema.sql](./database/schema.sql) for complete schema.

### Main Tables

- `users` - User accounts
- `videos` - Video metadata
- `votes` - Like/Not-Like votes
- `user_liked_videos` - Saved videos
- `views` - Video view tracking
- `reports` - Content reports

## Recommendation Algorithm

See [RECOMMENDATION_ALGORITHM.md](./RECOMMENDATION_ALGORITHM.md) for detailed algorithm specification.

The algorithm personalizes the feed based on:
- Creator-based similarity (40%)
- Content-based similarity (30%)
- Engagement-based similarity (20%)
- Temporal factors (10%)

## Development Roadmap

### MVP (Weeks 1-6)
- [x] Project structure and documentation
- [ ] Backend API implementation
- [ ] Database setup and migrations
- [ ] Authentication system
- [ ] Video upload and processing
- [ ] Frontend feed and swipe UI
- [ ] Recommendation algorithm
- [ ] Admin dashboard

### Phase 2
- [ ] Push notifications
- [ ] User profiles and following
- [ ] Comments and interactions
- [ ] Advanced analytics
- [ ] Machine learning recommendations

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

[Add your license here]

## Support

For issues and questions, please open an issue on GitHub.

