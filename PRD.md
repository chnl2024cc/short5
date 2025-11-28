# **PRD – Short-Video Platform (Nuxt 4 + FastAPI)**

## 1. Executive Summary

Ziel: Entwicklung einer **Short-Video Plattform** mit TikTok-ähnlicher UX für mobile Geräte. Nutzer können:

* Accounts erstellen
* Kurzvideos hochladen
* Andere Videos ansehen
* Videos nach rechts swipen (**Like**) oder links (**Nicht-Like**)

Likes beeinflussen personalisierte Empfehlungen, Nicht-Likes reduzieren ähnliche Inhalte.

Technischer Stack:

* **Frontend:** Nuxt 4 (PWA, Mobile-first)
* **Backend:** FastAPI (Python, Async)
* **Video-Pipeline:** FFmpeg Worker, HLS/Thumbnails
* **Storage/CDN:** S3 / Cloudflare R2 + CDN
* **DB:** PostgreSQL + ORM
* **Background Jobs:** Redis + Celery / RQ

---

## 2. User Stories

1. **Als Nutzer** möchte ich mich registrieren und einloggen, um Videos hochladen und ansehen zu können.
2. **Als Nutzer** möchte ich Videos durch vertikales Scrollen ansehen.
3. **Als Nutzer** möchte ich Videos nach rechts swipen → Like, nach links swipen → Nicht-Like.
4. **Als Nutzer** möchte ich ein kurzes Profil haben, meine hochgeladenen Videos und Likes/Nicht-Likes einsehen.
5. **Als Admin** möchte ich Uploads moderieren und Reports verwalten.
6. **Als System** soll das Feed-Algorithmus Likes bevorzugen und Nicht-Likes entwerten.

---

## 3. Features

| Feature                  | Beschreibung                                                                   | Priorität |
| ------------------------ | ------------------------------------------------------------------------------ | --------- |
| Auth & User Management   | Registrierung, Login, JWT Token, Passwort-Reset                                | Hoch      |
| Upload                   | Chunked Upload, Video-Metadaten speichern, Status (processing/ready)           | Hoch      |
| Video-Transcoding        | FFmpeg Worker erzeugt HLS + Thumbnail                                          | Hoch      |
| Feed                     | Infinite Scroll, vertikales Swipe-Interface, Like/Nicht-Like                   | Hoch      |
| Swipe Mechanik           | Rechts = Like, Links = Nicht-Like                                              | Hoch      |
| Recommendation Engine    | Likes erhöhen ähnliche Videos im Feed, Nicht-Likes reduzieren ähnliche Inhalte | Mittel    |
| Admin / Moderation       | Video Reports, User Reports, Content-Moderation                                | Mittel    |
| Video Storage/CDN        | S3/R2 Storage, HLS-CDN Streaming                                               | Hoch      |
| Analytics                | Views, Likes, Watch Time pro Video/User                                        | Mittel    |
| Notifications (optional) | Neue Videos, Trends, Follower Activity                                         | Niedrig   |

---

## 4. Technical Requirements

* **Frontend:** Nuxt 4 + TypeScript + Tailwind CSS + PWA
* **Backend:** FastAPI + Python 3.11, async endpoints
* **Database:** PostgreSQL, ORM (Tortoise ORM oder SQLAlchemy)
* **Background Jobs:** Redis + Celery/RQ für Transcoding
* **Video Processing:** FFmpeg Docker Worker, erzeugt HLS + Thumbnails
* **Storage/CDN:** Cloudflare R2 + Edge CDN
* **Auth:** JWT oder OAuth (Clerk / Keycloak optional)
* **Feed API:** Cursor-based Pagination für infinite scroll

---

## 5. DB Schema (Minimal)

### Users

```sql
id | username | email | password_hash | created_at
```

### Videos

```sql
id | user_id | title | description | status | url_hls | url_mp4 | thumbnail | created_at
```

### Likes

```sql
id | user_id | video_id | direction ('like'/'not_like') | created_at
```

### Views

```sql
id | video_id | user_id | watched_seconds | created_at
```

---

## 6. MVP Scope

* Vertikaler Swipe-Feed
* Upload / Transcoding / Storage
* User Auth
* Like / Nicht-Like Mechanik
* Infinite Scroll Feed
* Admin Dashboard minimal
* DB + Worker + CDN
* Feed-Algorithmus: Likes fördern ähnliche Inhalte, Nicht-Likes reduzieren sie

---
