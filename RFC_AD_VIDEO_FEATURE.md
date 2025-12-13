# RFC: Ad Video Feature

## Overview
This RFC describes the implementation of a special "Ad Video" feature that allows admin users to upload videos with an associated external link (typically an affiliate link). When an ad link is set, the video gets special playback behavior: it cannot be skipped for the first 5 seconds, and clicking on the video opens the ad link in a new window. The video title also becomes a clickable link to the ad offer.

## Status
**Approved** - Ready for Implementation

## Motivation
Enable monetization through affiliate links and sponsored content while maintaining a good user experience. Ad videos need to be clearly distinguishable and have specific interaction behaviors to ensure ad visibility and click-through.

## Requirements

### Functional Requirements

1. **Admin-Only Ad Link Field**
   - Only admin users can set an ad link when uploading a video
   - Regular users cannot see or set the ad link field
   - Ad link is optional (videos without ad link behave normally)

2. **Video Playback Behavior (when ad_link is set)**
   - Video cannot be skipped/swiped away for the first 5 seconds
   - After 5 seconds, users can skip/swipe to the next video
   - **ALL interaction with the ad video is disabled** - users cannot like, not_like, or share ad videos
   - Visual indicator should show remaining time before skipping is allowed

3. **Click Behavior (when ad_link is set)**
   - Clicking anywhere on the video opens the ad link in a new window/tab immediately (simplest approach)
   - This overrides the normal play/pause toggle behavior
   - **ALL action buttons (like, not_like, share) are HIDDEN for ad videos** - no interaction buttons should be visible
   - Users can only:
     - Click the video to open the ad link
     - Click the title (which is a link) to open the ad link
     - Click the "Go to Offer" button to open the ad link
     - Skip/swipe to next video after 5 seconds (but cannot interact with the ad video itself)

4. **Title Link (when ad_link is set)**
   - Video title becomes a clickable link
   - Clicking the title opens the ad link in a new window/tab
   - Visual styling should indicate it's a link (e.g., underline, different color)

5. **"Go to Offer" Button**
   - Add a prominent button (e.g., "Go to Offer" or better title) that opens the ad link
   - Button should be visible and easily accessible on ad videos
   - Button opens link in new window/tab

6. **Video Duration Validation**
   - Admin users cannot upload ad videos shorter than 5 seconds
   - Backend validation must enforce minimum 5-second duration for videos with ad_link
   - Error message should clearly indicate the minimum duration requirement

7. **Backward Compatibility**
   - Videos without ad_link continue to work exactly as before
   - No changes to existing video upload/playback flow for non-ad videos

### Technical Requirements

1. **Database Schema**
   - Add `ad_link` column to `videos` table (TEXT, nullable)
   - Add database migration

2. **Backend API**
   - Update video upload endpoint to accept `ad_link` parameter (admin-only)
   - Update video response schema to include `ad_link` field
   - Add validation for URL format
   - Add validation for minimum 5-second video duration when ad_link is set

3. **Frontend**
   - Update upload form to show ad_link field only for admin users
   - Update video player component to handle ad video behavior
   - **Hide ALL action buttons (like, not_like, share) for ad videos** - no interaction buttons visible
   - Prevent ALL swipe gestures (like, not_like, share) for ad videos - users can only skip to next video after 5 seconds
   - Add "Go to Offer" button for ad videos
   - Update video type definitions

4. **Analytics**
   - Check if ad link clicks can be combined with existing analytics
   - If not, create separate ad analytics tracking
   - Add separate "Ad Analytics" tab in Admin Panel

## Implementation Plan

### Phase 1: Database & Backend Schema

#### 1.1 Database Migration
**File**: `database/migrations/003_add_ad_link_to_videos.sql`

```sql
-- Migration: 003_add_ad_link_to_videos.sql
-- Description: Add ad_link field to videos table for affiliate/sponsored content

BEGIN;

ALTER TABLE videos 
ADD COLUMN IF NOT EXISTS ad_link TEXT;

-- Add index for querying videos with ad links (optional, for analytics)
CREATE INDEX IF NOT EXISTS idx_videos_ad_link ON videos(ad_link) WHERE ad_link IS NOT NULL;

COMMIT;
```

#### 1.2 Backend Model Update
**File**: `backend/app/models/video.py`

Add to `Video` class:
```python
ad_link = Column(Text, nullable=True)  # External link for ad videos (affiliate links, etc.)
```

#### 1.3 Backend Schema Update
**File**: `backend/app/schemas/video.py`

Update `VideoBase`:
```python
class VideoBase(BaseModel):
    title: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    ad_link: Optional[str] = Field(None, description="External ad link (admin only)")  # NEW
```

Update `VideoResponse`:
```python
class VideoResponse(VideoBase):
    # ... existing fields ...
    ad_link: Optional[str] = None  # NEW - included from VideoBase
```

#### 1.4 Backend API Update
**File**: `backend/app/api/v1/videos.py`

Update `upload_video` endpoint:
```python
@router.post("/upload", status_code=status.HTTP_202_ACCEPTED)
async def upload_video(
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    ad_link: Optional[str] = Form(None),  # NEW
    current_user: User = Depends(get_current_user_required),
    db: AsyncSession = Depends(get_db),
):
    """Upload a video file"""
    
    # Validate ad_link - only admins can set it
    if ad_link and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can set ad_link",
        )
    
    # Validate URL format if ad_link is provided
    if ad_link:
        from urllib.parse import urlparse
        try:
            result = urlparse(ad_link)
            if not all([result.scheme, result.netloc]):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid URL format for ad_link",
                )
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid URL format for ad_link",
            )
    
    # ... existing file validation ...
    
    # Note: Video duration validation for ad videos happens in video_worker
    # The worker will check if ad_link is set and duration < 5 seconds
    # If validation fails, video status will be set to FAILED with error_reason
    
    # Create video record
    video = Video(
        user_id=current_user.id,
        title=title,
        description=description,
        ad_link=ad_link if current_user.is_admin else None,  # Only set if admin
        status=VideoStatus.UPLOADING,
        file_size_bytes=file_size,
        original_filename=file.filename,
    )
    # ... rest of upload logic ...
```

Update `get_video` endpoint to include `ad_link`:
```python
return VideoResponse(
    # ... existing fields ...
    ad_link=video.ad_link,  # NEW
    # ... rest of fields ...
)
```

#### 1.5 Video Worker Duration Validation
**File**: `video_worker/worker.py`

Add validation after duration is extracted:
```python
# After getting metadata and duration (around line 678)
duration = metadata["duration"]

# Check if this is an ad video and validate minimum duration
with SessionLocal() as session:
    video_check = session.execute(
        text("SELECT ad_link FROM videos WHERE id = :video_id"),
        {"video_id": video_id}
    ).fetchone()
    
    if video_check and video_check[0]:  # ad_link is set
        if duration < 5.0:
            error_category = "VALIDATION_ERROR"
            user_friendly_error = f"Ad videos must be at least 5 seconds long. This video is {duration:.1f} seconds."
            print(f"✗ {user_friendly_error}")
            update_video_status(
                video_id, 
                "failed", 
                error_reason=user_friendly_error
            )
            raise ValueError(user_friendly_error)
```

#### 1.6 Prevent Likes on Ad Videos
**File**: `backend/app/api/v1/videos.py`

Update `vote_on_video` endpoint:
```python
@router.post("/{video_id}/vote", response_model=VoteResponse)
async def vote_on_video(
    video_id: str,
    vote_data: VoteRequest,
    current_user: Optional[User] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Swipe/vote on a video (Like or Not-Like) - supports both authenticated and anonymous votes"""
    # Check if video exists
    result = await db.execute(select(Video).where(Video.id == video_id))
    video = result.scalar_one_or_none()
    
    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video not found",
        )
    
    # Prevent liking ad videos
    if vote_data.direction == "like" and video.ad_link:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ad videos cannot be liked",
        )
    
    # ... rest of existing vote logic ...
```

### Phase 2: Frontend Type Definitions

#### 2.1 Update Video Type
**File**: `frontend/types/video.ts`

```typescript
export interface Video {
  id: string
  title?: string
  description?: string
  status: VideoStatus
  thumbnail: string
  url_mp4: string
  duration_seconds?: number | null
  error_reason?: string | null
  ad_link?: string | null  // NEW - External link for ad videos
  user: VideoUser
  stats: VideoStats
  created_at: string
}
```

### Phase 3: Frontend Upload Form

#### 3.1 Update Upload Form
**File**: `frontend/pages/upload.vue`

Add ad_link field (admin-only):
```vue
<!-- Ad Link Input (Admin Only) -->
<div v-if="authStore.user?.is_admin" class="space-y-2">
  <label for="ad_link" class="block text-sm font-medium text-gray-300 mb-2">
    {{ t('upload.adLinkLabel') }} <span class="text-xs text-gray-500">({{ t('upload.adminOnly') }})</span>
  </label>
  <input
    id="ad_link"
    v-model="form.ad_link"
    type="url"
    class="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
    :placeholder="t('upload.adLinkPlaceholder')"
    :disabled="uploading"
  />
  <p class="text-xs text-gray-500">
    {{ t('upload.adLinkHint') }}
  </p>
</div>
```

Update form data:
```typescript
const form = ref({
  title: '',
  description: '',
  ad_link: '',  // NEW
})
```

Update upload call:
```typescript
const uploadResponse = (await videosStore.uploadVideo(
  selectedFile.value,
  form.value.title || undefined,
  form.value.description || undefined,
  form.value.ad_link || undefined  // NEW
)) as { video_id: string; status: string; message?: string }
```

#### 3.2 Update Video Store
**File**: `frontend/stores/videos.ts`

Update `uploadVideo` method:
```typescript
async uploadVideo(
  file: File,
  title?: string,
  description?: string,
  ad_link?: string  // NEW
): Promise<{ video_id: string; status: string }> {
  const formData = new FormData()
  formData.append('file', file)
  if (title) formData.append('title', title)
  if (description) formData.append('description', description)
  if (ad_link) formData.append('ad_link', ad_link)  // NEW
  
  // ... rest of upload logic ...
}
```

#### 3.3 Add Translations
**File**: `frontend/locales/ru.ts` (and other locale files)

```typescript
upload: {
  // ... existing translations ...
  adLinkLabel: 'Ad Link (Affiliate)',
  adLinkPlaceholder: 'https://example.com/affiliate-link',
  adLinkHint: 'External link that opens when user clicks on the video. Admin only.',
  adminOnly: 'Admin Only',
}
```

### Phase 4: Frontend Video Player

#### 4.1 Update VideoSwiper Component
**File**: `frontend/components/VideoSwiper.vue`

Add ad video state and logic:

```typescript
// Ad video state
const isAdVideo = computed(() => !!props.video.ad_link)
const adSkipTimeRemaining = ref(5) // seconds
const canSkipAd = ref(false)
let adSkipInterval: NodeJS.Timeout | null = null

// Watch for ad video and initialize skip timer
watch(() => [props.video.ad_link, props.isActive], ([adLink, isActive]) => {
  if (adLink && isActive) {
    // Reset skip timer when ad video becomes active
    canSkipAd.value = false
    adSkipTimeRemaining.value = 5
    
    // Start countdown
    if (adSkipInterval) clearInterval(adSkipInterval)
    adSkipInterval = setInterval(() => {
      adSkipTimeRemaining.value--
      if (adSkipTimeRemaining.value <= 0) {
        canSkipAd.value = true
        if (adSkipInterval) {
          clearInterval(adSkipInterval)
          adSkipInterval = null
        }
      }
    }, 1000)
  } else {
    // Clean up interval
    if (adSkipInterval) {
      clearInterval(adSkipInterval)
      adSkipInterval = null
    }
    canSkipAd.value = true
  }
})

// Cleanup on unmount
onUnmounted(() => {
  if (adSkipInterval) {
    clearInterval(adSkipInterval)
  }
})
```

Update swipe handlers to prevent skipping during first 5 seconds:
```typescript
const endGesture = (e?: TouchEvent) => {
  // ... existing code ...
  
  // Prevent swipe if ad video and skip time hasn't elapsed
  if (isAdVideo.value && !canSkipAd.value) {
    // Don't process swipe - user must wait for skip timer
    return
  }
  
  // ... rest of gesture handling ...
}

// Also prevent vote on ad videos (they can't be liked)
const handleActionButtonClick = async (direction: 'like' | 'not_like' | 'share') => {
  // Prevent like action on ad videos
  if (direction === 'like' && isAdVideo.value) {
    return // Don't allow liking ad videos
  }
  
  // ... rest of existing logic ...
}
```

Update click handler to open ad link:
```typescript
const handleContainerClick = (e: MouseEvent) => {
  // ... existing swipe prevention code ...
  
  // If ad video, open ad link instead of toggling play/pause
  if (isAdVideo.value && props.video.ad_link) {
    e.preventDefault()
    e.stopPropagation()
    window.open(props.video.ad_link, '_blank', 'noopener,noreferrer')
    return
  }
  
  // ... existing play/pause logic ...
}
```

Add skip timer overlay in template (Netflix/YouTube style):
```vue
<!-- Ad Skip Timer Overlay (Netflix/YouTube style) -->
<div
  v-if="isAdVideo && !canSkipAd"
  class="absolute top-4 right-4 z-40"
>
  <button
    class="bg-black/90 text-white px-4 py-2 rounded-lg flex items-center gap-2 hover:bg-black transition-colors"
    disabled
  >
    <span class="text-sm font-medium">{{ t('videoSwiper.skipAd') }}</span>
    <span class="bg-white/20 px-2 py-1 rounded text-xs font-bold">
      {{ adSkipTimeRemaining }}
    </span>
  </button>
</div>
```

Update title and add "Go to Offer" button:
```vue
<!-- Video Info Overlay -->
<div class="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/60 to-transparent text-white z-30 video-info-overlay">
  <!-- Title as link for ad videos -->
  <a
    v-if="isAdVideo && video.ad_link"
    :href="video.ad_link"
    target="_blank"
    rel="noopener noreferrer"
    @click.stop
    class="font-bold text-lg hover:text-blue-400 underline cursor-pointer transition-colors block mb-2"
  >
    {{ video.title || 'Untitled' }}
  </a>
  <!-- Regular title for non-ad videos -->
  <h3
    v-else-if="video.title && video.title.trim() !== '' && video.title.toLowerCase() !== 'untitled'"
    class="font-bold text-lg mb-2"
  >
    {{ video.title }}
  </h3>
  <p class="text-sm mb-3">{{ video.user?.username }}</p>
  
  <!-- Action Buttons - HIDDEN for ad videos (only show views and "Go to Offer") -->
  <div class="flex gap-4 mt-2 text-sm items-center">
    <!-- Views count - Always visible -->
    <span>👁️ {{ video.stats?.views || 0 }}</span>
    
    <!-- Like count - HIDDEN for ad videos -->
    <span v-if="!isAdVideo">❤️ {{ video.stats?.likes || 0 }}</span>
    
    <!-- Share Button - HIDDEN for ad videos -->
    <button
      v-if="!isAdVideo"
      @click.stop="handleShare"
      class="flex items-center gap-1 px-3 py-1.5 bg-black/60 hover:bg-black/80 active:bg-black/90 rounded-lg transition-colors touch-manipulation"
      :title="t('videoSwiper.shareButton')"
    >
      <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.368 2.684 3 3 0 00-5.368-2.684z" />
      </svg>
      <span class="font-medium">{{ t('videoSwiper.shareButton') }}</span>
    </button>
    
    <!-- Go to Offer Button - Only for ad videos -->
    <a
      v-if="isAdVideo && video.ad_link"
      :href="video.ad_link"
      target="_blank"
      rel="noopener noreferrer"
      @click.stop="trackAdClick"
      class="flex items-center gap-1 px-4 py-2 bg-blue-600 hover:bg-blue-700 active:bg-blue-800 rounded-lg transition-colors touch-manipulation font-semibold"
    >
      <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
      </svg>
      <span>{{ t('videoSwiper.goToOffer') }}</span>
    </a>
    
    <!-- Report Button -->
    <button
      v-if="authStore.isAuthenticated"
      @click.stop="showReportDialog = true"
      class="flex items-center gap-1 px-3 py-1.5 bg-red-600/60 hover:bg-red-600/80 active:bg-red-600/90 rounded-lg transition-colors touch-manipulation"
      title="Report"
    >
      <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
      </svg>
      <span class="font-medium">Report</span>
    </button>
  </div>
</div>
```

#### 4.2 Update VideoFeed Component
**File**: `frontend/components/VideoFeed.vue`

Ensure swipe prevention works at feed level:
```typescript
const handleSwipe = (direction: 'like' | 'not_like' | 'share') => {
  const currentVideo = videos.value[currentIndex.value]
  
  // Prevent swipe if ad video and skip time hasn't elapsed
  if (currentVideo?.ad_link && !canSkipAd.value) {
    return // Don't process swipe
  }
  
  // ... existing swipe handling ...
}
```

#### 4.3 Add Translations
**File**: `frontend/locales/ru.ts`

```typescript
videoSwiper: {
  // ... existing translations ...
  skipAd: 'Skip Ad',
  goToOffer: 'Go to Offer',
  adVideoClickHint: 'Click to visit offer',
}
```

### Phase 5: Spring Boot Backend (if applicable)

If using Spring Boot backend, similar changes needed:

#### 5.1 Entity Update
**File**: `backend-spring/src/main/java/com/short5/entity/Video.java`

```java
@Column(name = "ad_link", columnDefinition = "TEXT")
private String adLink;
```

#### 5.2 DTO Update
**File**: `backend-spring/src/main/java/com/short5/dto/VideoDTO.java`

```java
private String adLink;
```

#### 5.3 Controller Update
**File**: `backend-spring/src/main/java/com/short5/controller/VideoController.java`

Add validation for admin-only ad_link in upload endpoint.

## Testing Plan

### Unit Tests

1. **Backend API Tests**
   - Test that non-admin users cannot set ad_link
   - Test that admin users can set ad_link
   - Test URL validation for ad_link
   - Test that ad_link is included in video response

2. **Frontend Component Tests**
   - Test that ad_link field only shows for admin users
   - Test that ad video cannot be skipped for first 5 seconds
   - Test that clicking ad video opens link in new window
   - Test that title is clickable link for ad videos

### Integration Tests

1. **End-to-End Upload Flow**
   - Admin uploads video with ad_link
   - Verify ad_link is saved in database
   - Verify video response includes ad_link

2. **End-to-End Playback Flow**
   - Load ad video in feed
   - Verify skip timer appears
   - Verify swipe is disabled for first 5 seconds
   - Verify swipe works after 5 seconds
   - Verify click opens ad link
   - Verify title is clickable

### Manual Testing Checklist

- [ ] Admin can see ad_link field in upload form
- [ ] Non-admin cannot see ad_link field
- [ ] Admin cannot upload ad video shorter than 5 seconds
- [ ] Ad video shows skip timer (Netflix/YouTube style) for first 5 seconds
- [ ] Ad video cannot be skipped/swiped for first 5 seconds
- [ ] Ad video can be skipped (swiped to next) after 5 seconds
- [ ] ALL action buttons (like, not_like, share) are HIDDEN for ad videos
- [ ] Ad videos cannot be liked, not_liked, or shared (all interactions blocked)
- [ ] Users can only click video/title/"Go to Offer" to open ad link or skip after 5 seconds
- [ ] Clicking ad video opens link in new window immediately
- [ ] Title is clickable link for ad videos
- [ ] "Go to Offer" button is visible and works on ad videos
- [ ] Regular videos (no ad_link) work as before
- [ ] URL validation works correctly
- [ ] Ad click analytics are tracked (if implemented)

## Security Considerations

1. **Admin-Only Access**
   - Backend must validate admin status before accepting ad_link
   - Frontend should hide field for non-admins, but backend is source of truth

2. **URL Validation**
   - Validate URL format to prevent XSS attacks
   - Use `noopener,noreferrer` when opening links in new window

3. **Data Privacy**
   - Ad links may contain affiliate tracking parameters
   - Ensure ad_link is only visible to users viewing the video (not in public APIs unless needed)

## Analytics Implementation

### Ad Link Click Tracking

We need to track ad link clicks separately. Options:

1. **Use existing ShareClick model** (if structure allows)
   - Check if ShareClick can be extended to track ad clicks
   - If yes, reuse existing analytics infrastructure

2. **Create new AdClick model** (if ShareClick doesn't fit)
   - New table: `ad_clicks` with fields:
     - `id` (UUID)
     - `video_id` (UUID, FK to videos)
     - `clicker_session_id` (UUID, for anonymous users)
     - `user_id` (UUID, nullable, FK to users)
     - `clicked_at` (timestamp)
   - Similar structure to ShareClick for consistency

3. **Admin Panel Tab**
   - Add "Ad Analytics" tab in admin panel
   - Show metrics:
     - Total ad clicks
     - Clicks per ad video
     - Click-through rate (CTR)
     - Clicks over time (daily/weekly)
     - Top performing ad videos

## Migration Strategy

1. **Database Migration**
   - Run migration to add `ad_link` column
   - Existing videos will have `NULL` ad_link (normal behavior)

2. **Backend Deployment**
   - Deploy backend changes first
   - Backend will accept ad_link but frontend won't send it yet

3. **Frontend Deployment**
   - Deploy frontend changes
   - Feature becomes available to admins immediately

4. **Rollback Plan**
   - If issues occur, can set `ad_link = NULL` for all videos
   - Frontend will gracefully handle missing ad_link field

## Timeline Estimate

- **Phase 1 (Database & Backend)**: 2-3 hours
- **Phase 2 (Frontend Types)**: 30 minutes
- **Phase 3 (Upload Form)**: 1-2 hours
- **Phase 4 (Video Player)**: 3-4 hours
- **Phase 5 (Spring Boot, if needed)**: 1-2 hours
- **Testing**: 2-3 hours
- **Total**: ~10-15 hours

## Success Criteria

1. ✅ Admin users can set ad_link when uploading videos
2. ✅ Admin cannot upload ad videos shorter than 5 seconds
3. ✅ Ad videos cannot be skipped for first 5 seconds (Netflix/YouTube style timer)
4. ✅ Like button is hidden for ad videos
5. ✅ Ad videos cannot be liked or added to liked videos
6. ✅ Clicking ad video opens link in new window immediately
7. ✅ Title is clickable link for ad videos
8. ✅ "Go to Offer" button is visible and functional
9. ✅ Regular videos continue to work normally
10. ✅ No breaking changes to existing functionality
11. ✅ Ad click analytics tracked (if implemented)

## References

- Current video upload flow: `frontend/pages/upload.vue`
- Current video player: `frontend/components/VideoSwiper.vue`
- Video model: `backend/app/models/video.py`
- Video API: `backend/app/api/v1/videos.py`

