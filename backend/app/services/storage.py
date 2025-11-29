"""
Storage service for handling file operations (S3/R2 and local)
"""
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

from app.core.config import settings

# Try to import boto3 - make it optional
try:
    import boto3
    from botocore.exceptions import ClientError
    BOTO3_AVAILABLE = True
except ImportError:
    BOTO3_AVAILABLE = False
    ClientError = Exception  # Fallback for type hints


class StorageService:
    """Service for managing video files in storage"""
    
    def __init__(self):
        self.s3_client = None
        self.s3_bucket = settings.S3_BUCKET_NAME
        self.s3_endpoint_url = settings.S3_ENDPOINT_URL
        
        # Initialize S3 client if credentials are available and boto3 is available
        if BOTO3_AVAILABLE and settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY:
            try:
                self.s3_client = boto3.client(
                    "s3",
                    endpoint_url=self.s3_endpoint_url or None,
                    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                    region_name=settings.AWS_REGION,
                )
            except Exception as e:
                print(f"Warning: Failed to initialize S3 client: {e}. Will use local storage.")
                self.s3_client = None
    
    def is_s3_mode(self) -> bool:
        """Check if using S3/R2 storage"""
        return self.s3_client is not None and self.s3_bucket
    
    def extract_s3_key_from_url(self, url: str) -> Optional[str]:
        """Extract S3 key from a storage URL"""
        if not url:
            return None
        
        # Handle different URL formats:
        # - https://bucket.s3.region.amazonaws.com/key
        # - https://endpoint/bucket/key
        # - /uploads/processed/key (local)
        
        # Local file path
        if url.startswith("/"):
            return None
        
        parsed = urlparse(url)
        path = parsed.path.lstrip("/")
        
        # Remove bucket name from path if present
        if self.s3_bucket and path.startswith(f"{self.s3_bucket}/"):
            return path[len(f"{self.s3_bucket}/"):]
        
        return path
    
    def delete_from_s3(self, key: str) -> bool:
        """Delete a single file from S3/R2"""
        if not self.s3_client:
            return False
        try:
            self.s3_client.delete_object(Bucket=self.s3_bucket, Key=key)
            return True
        except ClientError as e:
            print(f"Error deleting S3 object {key}: {e}")
            return False
    
    def delete_prefix_from_s3(self, prefix: str) -> int:
        """Delete all objects with a given prefix from S3/R2"""
        if not self.s3_client:
            return 0
        deleted_count = 0
        try:
            paginator = self.s3_client.get_paginator("list_objects_v2")
            pages = paginator.paginate(Bucket=self.s3_bucket, Prefix=prefix)
            
            for page in pages:
                if "Contents" not in page:
                    continue
                
                objects = [{"Key": obj["Key"]} for obj in page["Contents"]]
                if objects:
                    response = self.s3_client.delete_objects(
                        Bucket=self.s3_bucket,
                        Delete={"Objects": objects}
                    )
                    deleted_count += len(response.get("Deleted", []))
            
            return deleted_count
        except ClientError as e:
            print(f"Error deleting S3 prefix {prefix}: {e}")
            return deleted_count
    
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
            video_urls: Dict with keys like 'url_hls', 'url_mp4', 'thumbnail'
        
        Returns:
            Dict with deletion results
        """
        results = {
            "deleted_files": [],
            "failed_files": [],
            "mode": "s3" if self.is_s3_mode() else "local"
        }
        
        if self.is_s3_mode():
            # S3/R2 mode: Delete entire prefix
            prefix = f"videos/{video_id}/"
            deleted_count = self.delete_prefix_from_s3(prefix)
            if deleted_count > 0:
                results["deleted_files"].append(f"{prefix}* ({deleted_count} objects)")
            
            # Also delete MP4 if it exists separately
            if video_urls.get("url_mp4"):
                mp4_key = self.extract_s3_key_from_url(video_urls["url_mp4"])
                if mp4_key and not mp4_key.startswith(f"videos/{video_id}/"):
                    if self.delete_from_s3(mp4_key):
                        results["deleted_files"].append(mp4_key)
                    else:
                        results["failed_files"].append(mp4_key)
        else:
            # Local storage mode
            # Delete processed files
            processed_dir = Path("/app/uploads/processed")
            if processed_dir.exists():
                pattern = f"*{video_id}*"
                deleted_count = self.delete_local_files_by_pattern(processed_dir, pattern)
                if deleted_count > 0:
                    results["deleted_files"].append(f"{pattern} ({deleted_count} files)")
            
            # Delete original uploaded file
            upload_dir = Path("/app/uploads")
            if upload_dir.exists():
                # Try common extensions
                for ext in [".mp4", ".mov", ".avi"]:
                    file_path = upload_dir / f"{video_id}{ext}"
                    if file_path.exists():
                        if self.delete_local_file(file_path):
                            results["deleted_files"].append(str(file_path))
                            break
            
            # Delete temp processing directory
            temp_dir = Path(f"/tmp/video_processing/{video_id}")
            if temp_dir.exists():
                import shutil
                try:
                    shutil.rmtree(temp_dir, ignore_errors=True)
                    results["deleted_files"].append(f"temp directory: {temp_dir}")
                except Exception as e:
                    results["failed_files"].append(f"temp directory: {e}")
        
        return results


# Global instance
storage_service = StorageService()
