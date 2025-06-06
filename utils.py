import os
import time
import logging
from typing import Optional, Tuple, List
from PIL import Image
import ffmpeg
from config import COMPRESSION_SETTINGS, PREVIEW_SETTINGS

logger = logging.getLogger(__name__)

def compress_image(
    input_path: str,
    output_path: str,
    quality: str = 'medium'
) -> bool:
    """
    Compress an image file.
    
    Args:
        input_path: Path to input image
        output_path: Path to save compressed image
        quality: Compression quality (low, medium, high)
        
    Returns:
        bool: True if compression successful
    """
    try:
        settings = COMPRESSION_SETTINGS[quality]
        with Image.open(input_path) as img:
            img.save(
                output_path,
                quality=settings['quality'],
                optimize=True
            )
        return True
    except Exception as e:
        logger.error(f"Image compression failed: {str(e)}")
        return False

def compress_video(
    input_path: str,
    output_path: str,
    quality: str = 'medium'
) -> bool:
    """
    Compress a video file.
    
    Args:
        input_path: Path to input video
        output_path: Path to save compressed video
        quality: Compression quality (low, medium, high)
        
    Returns:
        bool: True if compression successful
    """
    try:
        settings = COMPRESSION_SETTINGS[quality]
        stream = ffmpeg.input(input_path)
        stream = ffmpeg.output(
            stream,
            output_path,
            vcodec='libx264',
            crf=settings['quality'],
            preset='medium'
        )
        ffmpeg.run(stream, overwrite_output=True)
        return True
    except Exception as e:
        logger.error(f"Video compression failed: {str(e)}")
        return False

def generate_preview(
    input_path: str,
    output_path: str,
    size: str = 'medium'
) -> bool:
    """
    Generate a preview image for a file.
    
    Args:
        input_path: Path to input file
        output_path: Path to save preview
        size: Preview size (small, medium, large)
        
    Returns:
        bool: True if preview generation successful
    """
    try:
        settings = PREVIEW_SETTINGS[size]
        if input_path.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp')):
            with Image.open(input_path) as img:
                img.thumbnail((settings['width'], settings['height']))
                img.save(output_path)
        elif input_path.lower().endswith(('.mp4', '.avi', '.mkv', '.mov')):
            stream = ffmpeg.input(input_path, ss=1)
            stream = ffmpeg.output(
                stream,
                output_path,
                vframes=1,
                s=f"{settings['width']}x{settings['height']}"
            )
            ffmpeg.run(stream, overwrite_output=True)
        return True
    except Exception as e:
        logger.error(f"Preview generation failed: {str(e)}")
        return False

def get_file_info(file_path: str) -> dict:
    """
    Get file information.
    
    Args:
        file_path: Path to file
        
    Returns:
        dict: File information
    """
    try:
        stat = os.stat(file_path)
        return {
            'size': stat.st_size,
            'created': stat.st_ctime,
            'modified': stat.st_mtime,
            'extension': os.path.splitext(file_path)[1].lower(),
            'name': os.path.basename(file_path)
        }
    except Exception as e:
        logger.error(f"Failed to get file info: {str(e)}")
        return {}

def generate_filename(
    original_name: str,
    pattern: str = '{original_name}_{timestamp}'
) -> str:
    """
    Generate a filename based on pattern.
    
    Args:
        original_name: Original filename
        pattern: Filename pattern
        
    Returns:
        str: Generated filename
    """
    try:
        name, ext = os.path.splitext(original_name)
        timestamp = int(time.time())
        return pattern.format(
            original_name=name,
            timestamp=timestamp
        ) + ext
    except Exception as e:
        logger.error(f"Filename generation failed: {str(e)}")
        return original_name

def split_file(
    input_path: str,
    chunk_size: int,
    output_dir: str
) -> List[str]:
    """
    Split a file into chunks.
    
    Args:
        input_path: Path to input file
        chunk_size: Size of each chunk in bytes
        output_dir: Directory to save chunks
        
    Returns:
        List[str]: List of chunk file paths
    """
    try:
        chunk_paths = []
        with open(input_path, 'rb') as f:
            chunk_num = 0
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                chunk_path = os.path.join(
                    output_dir,
                    f"{os.path.basename(input_path)}.part{chunk_num}"
                )
                with open(chunk_path, 'wb') as chunk_file:
                    chunk_file.write(chunk)
                chunk_paths.append(chunk_path)
                chunk_num += 1
        return chunk_paths
    except Exception as e:
        logger.error(f"File splitting failed: {str(e)}")
        return []

def merge_files(
    chunk_paths: List[str],
    output_path: str
) -> bool:
    """
    Merge file chunks.
    
    Args:
        chunk_paths: List of chunk file paths
        output_path: Path to save merged file
        
    Returns:
        bool: True if merge successful
    """
    try:
        with open(output_path, 'wb') as outfile:
            for chunk_path in chunk_paths:
                with open(chunk_path, 'rb') as infile:
                    outfile.write(infile.read())
        return True
    except Exception as e:
        logger.error(f"File merging failed: {str(e)}")
        return False 