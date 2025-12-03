# RFC – Short-Video Plattform (Nuxt 4 + FastAPI)

## 1. Context
Wir bauen eine self-hosted, mobile-first Short-Video Plattform ähnlich TikTok:

- **Frontend:** Nuxt 4 PWA  
- **Backend:** FastAPI  
- **Video Worker:** FFmpeg Docker Worker  
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
- **Video Sharing:** 
  - Share-Button in Video-Player, Profil-Seite und Liked-Videos
  - Format: `/?video=<video_id>` - geteilte Links springen direkt zum Video im Feed
  - Mobile: Nutzt Web Share API (native Share-Dialog)
  - Desktop: Kopiert Link in Zwischenablage mit Bestätigung
- **Upload Improvements:**
  - Auto-Fill: Titel wird automatisch aus Dateiname (ohne Extension) übernommen
  - Benutzer kann Titel vor Upload ändern
- **Error Handling:**
  - Videos ohne `url_mp4` werden übersprungen statt App-Crash
  - Graceful Degradation: Fehlende Thumbnails zeigen Placeholder
  - Feed lädt weiterhin, auch wenn einzelne Videos fehlerhaft sind
- **Feed Refresh:**
  - Refresh-Button auf leeren Feed-Seiten
  - Navigiert zu `/` für komplett frischen Feed-Start  

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
- Video danach lokal ausliefern  

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

### Storage

* Videos lokal gespeichert
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
4. **Video Sharing:** ✅ Implementiert - Share-Funktionalität mit `/?video=<video_id>` Links, Web Share API auf Mobile, Clipboard auf Desktop
5. **Upload UX:** ✅ Implementiert - Auto-Fill Titel aus Dateiname, benutzerfreundlicher Upload-Flow
6. **Error Resilience:** ✅ Implementiert - Videos ohne `url_mp4` werden übersprungen, App bleibt stabil

---

## 3.2. Video Sharing Feature

### Overview
Users can share videos with friends via shareable links. This enables viral growth and easy content distribution.

### Implementation

**Share URL Format:**
- Format: `http://localhost:3000/?video=<video_id>` (or production domain)
- When opened, the feed automatically jumps to the specified video
- Works for both authenticated and anonymous users

**Share Functionality:**
- **Share Button Locations:**
  - Video player overlay (always visible, touch-friendly)
  - Profile page (on user's own videos)
  - Liked videos page
- **Share Methods:**
  - **Mobile:** Uses Web Share API for native share dialog (WhatsApp, Messages, etc.)
  - **Desktop:** Copies link to clipboard with confirmation notification
  - **Fallback:** Shows URL in alert if clipboard API fails

**Technical Details:**
- Share button is always visible (not hover-only) for mobile compatibility
- Touch-optimized with proper sizing and feedback
- Preserves shared video links when navigating/refreshing feed
- Feed component automatically detects `?video=` query parameter and loads target video

---

## 3.3. Video Deletion Feature

### Overview
Users should be able to delete their own videos from their profile view. When a video is deleted, all associated data must be removed comprehensively:

1. **Database Records:**
   - Video record (CASCADE deletes handle related records automatically):
     - Votes (likes/not-likes) - CASCADE
     - UserLikedVideos (saved list entries) - CASCADE
     - Views - CASCADE
   - Reports related to the video should be handled (mark as resolved or delete)

2. **Storage Files:**
   - **Local Storage:**
     - Original uploaded file: `/app/uploads/originals/{video_id}.{ext}`
     - Processed MP4: `/app/uploads/processed/{video_id}/video.mp4`
     - Processed thumbnail: `/app/uploads/processed/{video_id}/thumbnail.jpg`
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
  2. Deletes all files from local storage
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
- Parse storage URLs to extract local file paths
- Delete all matching files locally for the video
- Handle local file system storage

---

## 4. Timeline Vorschlag (MVP)

* Woche 1–2: Backend + DB Setup + Auth
* Woche 2–3: Video Upload + FFmpeg Worker + Storage
* Woche 3–4: Nuxt 4 Frontend + Feed + Swipe + Preloading + Liked-Liste
* Woche 4–5: Admin Dashboard minimal + Moderation
* Woche 5–6: Testing + Deployment

---

## 5. Summary

* **Frontend:** Nuxt 4 PWA, Mobile-first, vertikaler Feed (ohne Login-Anforderung), Preload für smooth swipe, Overlay „LIKE/NOPE", Anonymous Voting mit localStorage-Speicherung, Video-Sharing mit `/?video=<id>` Links, Auto-Fill Titel aus Dateiname, Error-Handling für fehlerhafte Videos
* **Backend:** FastAPI, Async REST API, JWT Auth (optional für Feed), Video/Feed/Admin Modules, Liked-/Saved-Liste, Vote-Synchronisation
* **Video Worker:** FFmpeg Docker, MP4 Transcoding + Thumbnail, Queue via Celery/RQ
* **DB:** PostgreSQL + ORM, inkl. UserLikedVideos
* **Storage:** Lokale Dateispeicherung
* **Feed Algorithm:** Tinder-like Swipe: Rechts = Like / Saved-Liste, Links = Nicht-Like, beeinflusst Empfehlungen
* **UX-Hinweis:** Standard Tinder-Swipe übernommen → intuitive Nutzererfahrung
* **User Acquisition:** Anonymous Access ermöglicht maximale Reichweite für geteilte Links, Votes werden nach Account-Erstellung synchronisiert
* **Content Sharing:** Share-Funktionalität ermöglicht einfache Verbreitung von Videos über Messaging-Apps und Social Media

