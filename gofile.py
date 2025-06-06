import os
import json
import shlex
import logging
import requests
import subprocess
from typing import Dict, Optional, Union
from pyrogram.types import Message

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class GoFileError(Exception):
    """Base exception for GoFile related errors"""
    pass

class GoFileAPIError(GoFileError):
    """Exception raised for GoFile API errors"""
    pass

class GoFileUploadError(GoFileError):
    """Exception raised for GoFile upload errors"""
    pass

def get_server() -> str:
    """Get the best available GoFile server."""
    try:
        response = requests.get("https://api.gofile.io/servers/")
        response.raise_for_status()
        data = response.json()
        servers = data["data"]["servers"]
        return servers[0]["name"]
    except Exception as e:
        logger.error(f"Failed to get GoFile server: {str(e)}")
        raise GoFileAPIError("Failed to get GoFile server")

def uploadFile(file_path: str, token: Optional[str] = None, folderId: Optional[str] = None) -> Dict[str, Union[str, int]]:
    """
    Upload a file to GoFile.
    
    Args:
        file_path (str): Path to the file to upload
        token (Optional[str]): GoFile token for authenticated uploads
        folderId (Optional[str]): GoFile folder ID for organizing uploads
        
    Returns:
        Dict[str, Union[str, int]]: Upload response data
        
    Raises:
        GoFileError: If upload fails
        GoFileAPIError: If API request fails
        GoFileUploadError: If file upload fails
    """
    try:
        server = get_server()
        upload_url = f"https://{server}.gofile.io/uploadFile"
        
        # Prepare the files and data for the request
        files = {
            'file': (os.path.basename(file_path), open(file_path, 'rb'))
        }
        data = {}
        if token:
            data['token'] = token
        if folderId:
            data['folderId'] = folderId
            
        logger.info(f"Uploading file {file_path} to GoFile")
        
        # Make the upload request
        response = requests.post(upload_url, files=files, data=data)
        response.raise_for_status()
        
        try:
            os.remove(file_path)
            logger.info(f"Temporary file {file_path} removed")
        except Exception as e:
            logger.warning(f"Failed to remove temporary file {file_path}: {str(e)}")
            
        try:
            response_data = response.json()
        except json.JSONDecodeError:
            raise GoFileAPIError("Invalid JSON response from GoFile")
            
        if not response_data:
            raise GoFileAPIError("Empty response from GoFile")
            
        if response_data["status"] == "ok":
            logger.info(f"File {file_path} uploaded successfully")
            return response_data["data"]
        elif "error-" in response_data["status"]:
            error = response_data["status"].split("-")[1]
            raise GoFileAPIError(f"GoFile API error: {error}")
        else:
            raise GoFileAPIError(f"Unknown GoFile API response: {response_data['status']}")
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Upload request failed: {str(e)}")
        raise GoFileUploadError(f"Upload request failed: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error during upload: {str(e)}")
        raise GoFileError(f"Upload failed: {str(e)}")
    finally:
        # Ensure the file is closed
        if 'files' in locals():
            files['file'][1].close()

def parse_upload_command(command: str, reply_message: Optional[Message] = None) -> tuple:
    """Parse upload command to extract URL, token, and folder ID."""
    parts = command.split()
    if len(parts) == 1:
        return None, None, None
    elif len(parts) == 2:
        return parts[1], None, None
    elif len(parts) == 3:
        return parts[1], parts[2], None
    else:
        raise ValueError("Invalid upload command format")
