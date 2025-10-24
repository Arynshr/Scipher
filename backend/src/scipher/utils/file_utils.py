from pathlib import Path
import shutil
import uuid
from typing import Optional
from fastapi import UploadFile

from scipher.config import settings
from scipher.core.exceptions import FileOperationException


class FileManager:
    """Handles all file system operations"""
    
    def __init__(self, upload_dir: Path = None):
        self.upload_dir = upload_dir or settings.UPLOAD_DIR
        self.ensure_upload_directory()
    
    def ensure_upload_directory(self):
        """Create upload directory if it doesn't exist"""
        try:
            self.upload_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            raise FileOperationException("directory creation", str(e))
    
    def generate_unique_filename(self, original_filename: str) -> tuple:
        """
        Generate unique filename while preserving extension
        
        Args:
            original_filename: Original file name
            
        Returns:
            Tuple of (unique_id, safe_filename)
        """
        doc_id = str(uuid.uuid4())
        file_ext = Path(original_filename).suffix.lower()
        safe_filename = f"{doc_id}{file_ext}"
        return doc_id, safe_filename
    
    def save_upload_file(
        self,
        file: UploadFile,
        filename: str
    ) -> Path:
        """
        Save uploaded file to disk
        
        Args:
            file: FastAPI UploadFile object
            filename: Target filename
            
        Returns:
            Path to saved file
            
        Raises:
            FileOperationException: If save fails
        """
        file_path = self.upload_dir / filename
        
        try:
            with file_path.open("wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            return file_path
        except Exception as e:
            # Cleanup partial file
            if file_path.exists():
                file_path.unlink()
            raise FileOperationException("save", str(e))
    
    def delete_file(self, file_path: str | Path) -> bool:
        """
        Delete file from disk
        
        Args:
            file_path: Path to file
            
        Returns:
            True if deleted, False if file didn't exist
            
        Raises:
            FileOperationException: If deletion fails
        """
        try:
            path = Path(file_path)
            if path.exists():
                path.unlink()
                return True
            return False
        except Exception as e:
            raise FileOperationException("delete", str(e))
    
    def get_file_size(self, file_path: str | Path) -> int:
        """
        Get file size in bytes
        
        Args:
            file_path: Path to file
            
        Returns:
            File size in bytes
            
        Raises:
            FileOperationException: If file doesn't exist
        """
        try:
            return Path(file_path).stat().st_size
        except FileNotFoundError:
            raise FileOperationException("stat", "File not found")
        except Exception as e:
            raise FileOperationException("stat", str(e))
    
    def read_file(self, file_path: str | Path) -> bytes:
        """
        Read file contents
        
        Args:
            file_path: Path to file
            
        Returns:
            File contents as bytes
            
        Raises:
            FileOperationException: If read fails
        """
        try:
            return Path(file_path).read_bytes()
        except Exception as e:
            raise FileOperationException("read", str(e))
    
    def move_file(self, source: Path, destination: Path) -> Path:
        """
        Move file to new location
        
        Args:
            source: Source file path
            destination: Destination path
            
        Returns:
            Destination path
            
        Raises:
            FileOperationException: If move fails
        """
        try:
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(source), str(destination))
            return destination
        except Exception as e:
            raise FileOperationException("move", str(e))


# Singleton instance
file_manager = FileManager()
