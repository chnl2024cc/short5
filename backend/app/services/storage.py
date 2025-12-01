"""
Storage service for handling local file operations
"""
from pathlib import Path
import shutil


class StorageService:
    """Service for managing video files in local storage"""
    
    def delete_local_file(self, file_path: Path) -> bool:
        """Delete a local file"""
        try:
            if file_path.exists() and file_path.is_file():
                file_path.unlink()
                return True
        except Exception as e:
            print(f"Error deleting local file {file_path}: {e}")
        return False
    
    def delete_local_files_by_pattern(self, directory: Path, pattern: str) -> int:
        """Delete all files matching a pattern in a directory"""
        deleted_count = 0
        try:
            if not directory.exists():
                return 0
            
            for file_path in directory.glob(pattern):
                if file_path.is_file():
                    try:
                        file_path.unlink()
                        deleted_count += 1
                    except Exception as e:
                        print(f"Error deleting {file_path}: {e}")
        except Exception as e:
            print(f"Error deleting local files by pattern: {e}")
        return deleted_count
    
    def delete_video_files(self, video_id: str, video_urls: dict) -> dict:
        """
        Delete all files associated with a video
        
        Args:
            video_id: UUID of the video
            video_urls: Dict with keys like 'url_mp4', 'thumbnail'
        
        Returns:
            Dict with deletion results
        """
        results = {
            "deleted_files": [],
            "failed_files": [],
            "mode": "local"
        }
        
        # Delete processed files (MP4, thumbnails)
        processed_dir = Path("/app/uploads/processed")
        if processed_dir.exists():
            # Delete entire video directory if it exists
            video_dir = processed_dir / video_id
            if video_dir.exists() and video_dir.is_dir():
                try:
                    shutil.rmtree(video_dir, ignore_errors=True)
                    results["deleted_files"].append(f"processed/{video_id}/")
                except Exception as e:
                    results["failed_files"].append(f"processed/{video_id}/: {e}")
            
            # Also try pattern matching as fallback
            pattern = f"*{video_id}*"
            deleted_count = self.delete_local_files_by_pattern(processed_dir, pattern)
            if deleted_count > 0:
                results["deleted_files"].append(f"{pattern} ({deleted_count} files)")
        
        # Delete original uploaded file
        originals_dir = Path("/app/uploads/originals")
        if originals_dir.exists():
            # Try common extensions
            for ext in [".mp4", ".mov", ".avi"]:
                file_path = originals_dir / f"{video_id}{ext}"
                if file_path.exists():
                    if self.delete_local_file(file_path):
                        results["deleted_files"].append(str(file_path))
                        break
        
        # Delete temp processing directory
        temp_dir = Path(f"/tmp/video_processing/{video_id}")
        if temp_dir.exists():
            try:
                shutil.rmtree(temp_dir, ignore_errors=True)
                results["deleted_files"].append(f"temp directory: {temp_dir}")
            except Exception as e:
                results["failed_files"].append(f"temp directory: {e}")
        
        return results


# Global instance
storage_service = StorageService()
