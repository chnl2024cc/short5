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
| Videos | Upload Handling, Status (processing/ready), Metadata |
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
  - Transcoding → HLS + mp4  
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
id | user_id | title | description | status | url_hls | url_mp4 | thumbnail | created_at
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
* HLS Streaming für Mobile / Edge Delivery
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

