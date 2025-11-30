#!/usr/bin/env python3
"""
Fix existing HLS master playlists to use correct BANDWIDTH format.

This script updates master playlists that were created with the old format
(BANDWIDTH=2500k) to the correct format (BANDWIDTH=2628000).
"""
import sys
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

VIDEO_PROFILES = {
    "720p": {
        "resolution": "1280x720",
        "bitrate": "2500k",
        "audio_bitrate": "128k",
    },
    "480p": {
        "resolution": "854x480",
        "bitrate": "1000k",
        "audio_bitrate": "96k",
    },
}


def parse_bitrate(bitrate_str: str) -> int:
    """Convert bitrate string (e.g., '2500k') to bits per second (integer)"""
    if bitrate_str.endswith('k'):
        return int(float(bitrate_str[:-1]) * 1000)  # Convert kbps to bps
    elif bitrate_str.endswith('M'):
        return int(float(bitrate_str[:-1]) * 1000000)  # Convert Mbps to bps
    else:
        # Assume it's already in bps
        return int(bitrate_str)


def fix_master_playlist(playlist_path: Path) -> bool:
    """Fix a master playlist file"""
    if not playlist_path.exists():
        print(f"  ⚠ Playlist not found: {playlist_path}")
        return False
    
    try:
        content = playlist_path.read_text()
        
        # Check if it's already in the correct format
        if 'BANDWIDTH=' in content and ',' in content.split('BANDWIDTH=')[1].split('\n')[0]:
            # Already has comma (likely has RESOLUTION), check if BANDWIDTH is numeric
            lines = content.split('\n')
            needs_fix = False
            for line in lines:
                if line.startswith('#EXT-X-STREAM-INF:BANDWIDTH='):
                    # Check if BANDWIDTH value ends with 'k' or 'M' (old format)
                    bandwidth_part = line.split('BANDWIDTH=')[1].split(',')[0]
                    if bandwidth_part.endswith('k') or bandwidth_part.endswith('M'):
                        needs_fix = True
                        break
            
            if not needs_fix:
                print(f"  ✓ Playlist already in correct format: {playlist_path.name}")
                return True
        
        # Rebuild the master playlist
        master_playlist_content = "#EXTM3U\n"
        for quality in VIDEO_PROFILES.keys():
            profile = VIDEO_PROFILES[quality]
            # Calculate total bandwidth (video + audio)
            video_bw = parse_bitrate(profile["bitrate"])
            audio_bw = parse_bitrate(profile["audio_bitrate"])
            total_bandwidth = video_bw + audio_bw
            
            # Include RESOLUTION for better compatibility
            resolution = profile["resolution"]
            
            # Create EXT-X-STREAM-INF tag with BANDWIDTH and RESOLUTION
            master_playlist_content += f'#EXT-X-STREAM-INF:BANDWIDTH={total_bandwidth},RESOLUTION={resolution}\n'
            # Extract video_id from playlist path
            video_id = playlist_path.parent.name
            master_playlist_content += f"{quality}/{video_id}.m3u8\n"
        
        # Write the fixed playlist
        playlist_path.write_text(master_playlist_content)
        print(f"  ✓ Fixed playlist: {playlist_path.name}")
        return True
        
    except Exception as e:
        print(f"  ✗ Error fixing playlist {playlist_path}: {e}")
        return False


def main():
    """Fix all master playlists in the processed videos directory"""
    processed_dir = Path("/app/uploads/processed/videos")
    
    if not processed_dir.exists():
        print(f"Error: Processed videos directory not found: {processed_dir}")
        print("Make sure you're running this script inside the backend container")
        return
    
    print(f"Scanning for master playlists in: {processed_dir}")
    print()
    
    fixed_count = 0
    skipped_count = 0
    error_count = 0
    
    # Find all playlist.m3u8 files
    for playlist_path in processed_dir.glob("*/playlist.m3u8"):
        video_id = playlist_path.parent.name
        print(f"Processing video: {video_id}")
        
        if fix_master_playlist(playlist_path):
            fixed_count += 1
        else:
            error_count += 1
        print()
    
    print(f"Summary:")
    print(f"  Fixed: {fixed_count}")
    print(f"  Errors: {error_count}")
    print(f"  Total: {fixed_count + error_count}")


if __name__ == "__main__":
    main()
