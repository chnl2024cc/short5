# RFC – Short-Video Plattform (Nuxt 4 + FastAPI)

## 1. Context
Wir bauen eine self-hosted, mobile-first Short-Video Plattform ähnlich TikTok:

- **Frontend:** Nuxt 4 PWA  
- **Backend:** FastAPI  
- **Video Worker:** FFmpeg Docker Worker  
- **Storage/CDN:** S3 / Cloudflare R2  
- **DB:** PostgreSQL + ORM  
- **Background Jobs:** Redis + Celery / RQ  

Ziel: **schnelles MVP**, skalierbar, modular erweiterbar, mit Tinder-artiger Swipe-Mechanik:

- **Rechts = Like / Zustimmung** → Video wird in persönlicher Liked-/Saved-Liste gespeichert, ähnliche Videos im Feed werden häufiger angezeigt  
- **Links = Nicht-Like / Pass** → ähnliche Videos im Feed werden reduziert  

---

## 2. Proposal

### Frontend (Nuxt 4)

- Mobile-first PWA, vertikaler Feed  
- **Anonymous Access:** Feed ist ohne Login zugänglich für maximale Reichweite (z.B. geteilte Links in Messengern)
- **Swipe-Mechanik:** Rechts = Like, Links = Nicht-Like (funktioniert auch ohne Account)
- **Anonymous Voting:** Votes ohne Account werden in localStorage gespeichert und nach Login/Registrierung automatisch synchronisiert  
- Infinite Scroll Feed  
- **Video Preloading:** Nächstes Video (Thumbnail/Cover) wird bereits im Hintergrund geladen → flüssiges Übergangserlebnis  
- Autoplay für aktuelles Video, andere pausiert  
- Calls Backend REST API:  
  - `/feed` (Cursor-basiert, optional auth)  
  - `/videos/upload` (erfordert Auth)  
  - `/videos/{id}/vote` (erfordert Auth, aber Votes werden lokal zwischengespeichert)  

**UX/Swipe-Details:**

- Beim Swipen erscheint visuelles Feedback:  
  - Overlay „LIKE" bei Rechts-Swipe  
  - Overlay „NOPE" bei Links-Swipe  
- Preloading: 1–2 Videos im Voraus, nächste Videos werden nachgeladen sobald nötig  
- Swipe-Aktion: 
  - **Mit Account:** POST `/videos/{id}/vote` mit direction = like | not_like (direkt)
  - **Ohne Account:** Vote wird in localStorage gespeichert, Sync nach Login/Registrierung  
- Geswiptes Video wird aus dem Feed entfernt, nächstes Video wird direkt angezeigt  
- Optional: Animation + smooth Übergang für Tinder-ähnliches Feeling  
- Onboarding: Erklärung der Swipe-Logik entfällt, da Tinder-Standard übernommen  

---

### Backend (FastAPI)

- Async REST API  
- Module:

| Modul | Aufgaben |
|-------|---------|
| Auth | JWT/OAuth, Registration, Login, Refresh Token, Vote-Synchronisation nach Login |
| Users | Profile, Stats, Creator Management, Liked-/Saved-Liste |
| Videos | Upload Handling, Status (processing/ready), Metadata, Deletion (with storage cleanup) |
| Feed | Likes/Nicht-Likes, Cursor Pagination, Recommendation Logic (optional auth) |
| Admin | Moderation, Reports, Content Review |

- **Feed Access:**  
  - `/feed` Endpoint unterstützt optional Authentication
  - Authentifizierte Nutzer: Personalisierter Feed (exkludiert bereits gevotete Videos)
  - Anonyme Nutzer: Öffentlicher Feed mit allen verfügbaren Videos
- **Recommendation Logic:**  
  - Likes → ähnliche Videos häufiger im Feed  
  - Nicht-Likes → ähnliche Videos seltener  
- **Liked-/Saved-Liste:**  
  - Rechts-Swipe speichert das Video in einer `UserLikedVideos` Tabelle  
- **Vote Synchronization:**  
  - Frontend sendet gespeicherte Votes nach Login/Registrierung
  - Backend verarbeitet Batch-Sync von localStorage Votes
- Background Jobs über Redis + Celery / RQ  

---

### Video Worker (FFmpeg)

- Docker Container, CPU-intensive Verarbeitung  
- Aufgaben:  
  - Transcoding → MP4  
  - Thumbnail + Preview erstellen  
  - Status Update DB → `ready`  
- Triggered über Queue (Celery/RQ)  
- Video danach auf CDN ausliefern  

---

### Database (PostgreSQL)

**Users**
```sql
id | username | email | password_hash | created_at
````

**Videos**

```sql
id | user_id | title | description | status | url_mp4 | thumbnail | created_at
```

**Likes / Swipes**

```sql
id | user_id | video_id | direction ('like'/'not_like') | created_at
```

**UserLikedVideos / Saved-Liste**

```sql
id | user_id | video_id | created_at
```

**Views**

```sql
id | video_id | user_id | watched_seconds | created_at
```

---

### Storage / CDN

* Videos auf S3 / Cloudflare R2
* MP4 Streaming mit standard Video-Tag
* Preload für nächste Videos im Frontend

---

## 3. Open Questions

1. Welche Bitraten / Formate initial erzeugen? (1080p, 720p, 480p)
2. Likes / Nicht-Likes → direkt Feed-Update oder batch-processed?
3. Admin-MVP-Funktionen: Reports nur oder zusätzlich User-Management?
4. Push Notifications → Phase 1 oder 2?

## 3.1. Resolved Questions

1. **Feed Access:** ✅ Implementiert - Feed ist ohne Login zugänglich für maximale Reichweite
2. **Anonymous Voting:** ✅ Implementiert - Votes werden in localStorage gespeichert und nach Login/Registrierung synchronisiert
3. **Vote Synchronization:** ✅ Implementiert - Automatische Sync nach erfolgreichem Login oder Registrierung

---

## 3.2. Video Deletion Feature

### Overview
Users should be able to delete their own videos from their profile view. When a video is deleted, all associated data must be removed comprehensively:

1. **Database Records:**
   - Video record (CASCADE deletes handle related records automatically):
     - Votes (likes/not-likes) - CASCADE
     - UserLikedVideos (saved list entries) - CASCADE
     - Views - CASCADE
   - Reports related to the video should be handled (mark as resolved or delete)

2. **Storage Files:**
   - **S3/R2 Storage (Production):**
     - HLS master playlist: `videos/{video_id}/playlist.m3u8`
     - HLS quality playlists: `videos/{video_id}/720p/{video_id}.m3u8`, `videos/{video_id}/480p/{video_id}.m3u8`
     - HLS video segments: All `.ts` files in `videos/{video_id}/{quality}/` directories
     - Thumbnail: `videos/{video_id}/thumbnail.jpg`
     - MP4 file (if exists): Based on `url_mp4` field
   - **Local Storage (Development):**
     - Original uploaded file: `/app/uploads/{video_id}.{ext}`
     - Processed files: All files in `/app/uploads/processed/` containing `{video_id}` in filename
     - Temporary processing files: `/tmp/video_processing/{video_id}/` directory

3. **Cache Invalidation:**
   - Redis cache keys related to the video (if any)
   - Feed cache entries containing the deleted video
   - User profile cache (video count stats)

4. **Background Jobs:**
   - Cancel any pending/processing Celery tasks for the video
   - Clean up any in-progress processing files

### Implementation Approach

**Backend:**
- Create a comprehensive video deletion service that:
  1. Extracts storage paths from video URLs
  2. Deletes all files from S3/local storage
  3. Invalidates relevant caches
  4. Deletes database record (CASCADE handles related records)
  5. Handles errors gracefully (continue deletion even if some files fail)

**Frontend:**
- Add delete button to video cards in profile view
- Show confirmation dialog before deletion
- Optimistic UI update (remove from list immediately)
- Error handling with rollback on failure

### API Endpoint
- `DELETE /api/v1/videos/{video_id}` - Already exists, needs enhancement
- Authorization: Only video owner or admin can delete
- Returns: Success message or error details

### Storage Cleanup Logic
- Parse storage URLs to extract S3 keys or local file paths
- Delete entire `videos/{video_id}/` prefix in S3 (or all matching files locally)
- Handle both production (S3/R2) and development (local file system) modes

---

## 4. Timeline Vorschlag (MVP)

* Woche 1–2: Backend + DB Setup + Auth
* Woche 2–3: Video Upload + FFmpeg Worker + Storage
* Woche 3–4: Nuxt 4 Frontend + Feed + Swipe + Preloading + Liked-Liste
* Woche 4–5: Admin Dashboard minimal + Moderation
* Woche 5–6: Testing + Deployment

---

## 5. Summary

* **Frontend:** Nuxt 4 PWA, Mobile-first, vertikaler Feed (ohne Login-Anforderung), Preload für smooth swipe, Overlay „LIKE/NOPE", Anonymous Voting mit localStorage-Speicherung
* **Backend:** FastAPI, Async REST API, JWT Auth (optional für Feed), Video/Feed/Admin Modules, Liked-/Saved-Liste, Vote-Synchronisation
* **Video Worker:** FFmpeg Docker, HLS + Thumbnail, Queue via Celery/RQ
* **DB:** PostgreSQL + ORM, inkl. UserLikedVideos
* **Storage/CDN:** S3 / Cloudflare R2
* **Feed Algorithm:** Tinder-like Swipe: Rechts = Like / Saved-Liste, Links = Nicht-Like, beeinflusst Empfehlungen
* **UX-Hinweis:** Standard Tinder-Swipe übernommen → intuitive Nutzererfahrung
* **User Acquisition:** Anonymous Access ermöglicht maximale Reichweite für geteilte Links, Votes werden nach Account-Erstellung synchronisiert

