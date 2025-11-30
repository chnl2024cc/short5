# Fix Master Playlist Format Issue

## Problem
Videos processed with the old code have master playlists with invalid `BANDWIDTH` format:
- ❌ Old: `BANDWIDTH=2500k` (string, invalid)
- ✅ New: `BANDWIDTH=2628000` (integer in bits per second, correct)

This causes HLS.js in Chrome to fail with "Video format not supported" error.

## Solution

### Step 1: Fix Existing Master Playlists

Run the fix script inside the backend container:

```powershell
docker-compose exec backend python /app/scripts/fix_master_playlists.py
```

This will:
- Scan all existing master playlists
- Update them to the correct format
- Include both video and audio bitrates in total BANDWIDTH
- Add RESOLUTION attribute for better compatibility

### Step 2: Verify the Fix

Check a specific video's master playlist:

```powershell
# View the fixed playlist
docker-compose exec backend cat /app/uploads/processed/videos/635614c3-935f-4b10-8fbf-b51e697e0ac4/playlist.m3u8
```

You should see:
```
#EXTM3U
#EXT-X-STREAM-INF:BANDWIDTH=2628000,RESOLUTION=1280x720
720p/635614c3-935f-4b10-8fbf-b51e697e0ac4.m3u8
#EXT-X-STREAM-INF:BANDWIDTH=1096000,RESOLUTION=854x480
480p/635614c3-935f-4b10-8fbf-b51e697e0ac4.m3u8
```

### Step 3: Test in Browser

1. Open Chrome DevTools (F12)
2. Go to Console tab
3. Try to play the video
4. Check for HLS error messages - they should now be more descriptive
5. The video should play correctly

## What Was Fixed

1. **Master Playlist Generation** (`video_worker/worker.py`):
   - Converts bitrate strings to integers
   - Includes video + audio bitrates in total BANDWIDTH
   - Adds RESOLUTION attribute

2. **Enhanced Error Logging** (`frontend/components/VideoSwiper.vue`):
   - Better HLS.js error messages
   - Specific warnings for manifest parsing errors
   - Helpful instructions in console

3. **Fix Script** (`backend/scripts/fix_master_playlists.py`):
   - Automatically fixes all existing playlists
   - Safe to run multiple times

## Notes

- **New videos**: Will automatically use the correct format**
- **Existing videos**: Need to run the fix script (or reprocess)
- **The fix script is idempotent**: Safe to run multiple times

## Troubleshooting

If the error persists after running the fix script:

1. **Check browser console** for specific HLS.js error messages
2. **Verify playlist format** using the cat command above
3. **Check network tab** to see if the playlist is being loaded correctly
4. **Try hard refresh** (Ctrl+Shift+R) to clear browser cache
