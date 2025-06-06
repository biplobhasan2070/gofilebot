import os
from dotenv import load_dotenv
from pyrogram.types import BotCommand

# Load environment variables
load_dotenv()

# Bot Configuration
BOT_TOKEN = ("1701354729:AAEPJFQ9Uw3p__1bwReWjBw9dt9u6c36uvc")
API_ID = int(("5310709"))
API_HASH = ("63a546bdaf18e2cbba99f87b4274fa05")

# File Upload Configuration
MAX_FILE_SIZE = 1024 * 1024 * 1024  # 1GB
ALLOWED_EXTENSIONS = {
    'images': ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp', 'tiff', 'ico'],
    'videos': ['mp4', 'avi', 'mkv', 'mov', 'wmv', 'flv', 'webm', 'm4v'],
    'documents': ['pdf', 'doc', 'docx', 'txt', 'rtf', 'odt', 'xls', 'xlsx', 'ppt', 'pptx'],
    'audio': ['mp3', 'wav', 'ogg', 'm4a', 'flac', 'aac'],
    'archives': ['zip', 'rar', '7z', 'tar', 'gz', 'bz2'],
    'other': ['apk', 'exe', 'iso', 'img']
}

# File Hosting Services Configuration
FILE_HOSTING_SERVICES = {
    'gofile': {
        'name': 'GoFile',
        'api_url': 'https://api.gofile.io',
        'upload_url': 'https://{server}.gofile.io/uploadFile',
        'download_url': 'https://{server}.gofile.io/download/{file_id}/{file_name}',
        'max_file_size': 1024 * 1024 * 1024,  # 1GB
        'supported_types': ['*'],
        'requires_auth': False
    },
    'bayfiles': {
        'name': 'BayFiles',
        'api_url': 'https://api.bayfiles.com',
        'upload_url': 'https://api.bayfiles.com/upload',
        'download_url': 'https://bayfiles.com/{file_id}',
        'max_file_size': 20 * 1024 * 1024,  # 20MB
        'supported_types': ['*'],
        'requires_auth': False
    }
}

# Bot Commands
BOT_COMMANDS = [
    BotCommand("start", "Start the bot"),
    BotCommand("help", "Show help message"),
    BotCommand("upload", "Upload file to GoFile"),
    BotCommand("cancel", "Cancel current operation"),
    BotCommand("status", "Check bot status"),
    BotCommand("settings", "Configure bot settings"),
    BotCommand("stats", "View upload statistics"),
    BotCommand("about", "About the bot"),
    BotCommand("hosts", "List available hosting services"),
    BotCommand("compress", "Compress file before upload"),
    BotCommand("batch", "Upload multiple files"),
    BotCommand("schedule", "Schedule file upload"),
    BotCommand("preview", "Generate file preview"),
    BotCommand("rename", "Rename file before upload"),
    BotCommand("split", "Split large file into parts"),
    BotCommand("merge", "Merge file parts"),
    BotCommand("convert", "Convert file format"),
    BotCommand("info", "Get file information")
]

# Bot Instructions
INSTRUCTIONS = """
I am a file uploader telegram bot. \
You can upload files to various hosting services with commands.

With media:
    Normal:
        `/upload`
    With token:
        `/upload token`
    With folder id:
        `/upload token folderid`

Using Link:
    Normal:
        `/upload url`
    With token:
        `/upload url token`
    With folder id:
        `/upload url token folderid`

Additional Commands:
    /help - Show this help message
    /cancel - Cancel current operation
    /status - Check bot status
    /settings - Configure bot settings
    /stats - View upload statistics
    /about - About the bot
    /hosts - List available hosting services
    /compress - Compress file before upload
    /batch - Upload multiple files
    /schedule - Schedule file upload
    /preview - Generate file preview
    /rename - Rename file before upload
    /split - Split large file into parts
    /merge - Merge file parts
    /convert - Convert file format
    /info - Get file information
"""

# Error Messages
ERROR_MESSAGES = {
    'invalid_url': 'Error: Invalid URL format',
    'no_media': 'Error: No downloadable media or URL found',
    'file_too_large': 'Error: File size exceeds the maximum limit',
    'invalid_file_type': 'Error: File type not supported',
    'upload_failed': 'Error: File upload failed',
    'api_error': 'Error: API error occurred',
    'operation_cancelled': 'Operation cancelled by user',
    'no_active_operation': 'No active operation to cancel',
    'invalid_command': 'Invalid command. Use /help to see available commands',
    'service_unavailable': 'Error: Selected hosting service is unavailable',
    'compression_failed': 'Error: File compression failed',
    'batch_upload_failed': 'Error: Batch upload failed',
    'schedule_failed': 'Error: Failed to schedule upload',
    'preview_failed': 'Error: Failed to generate preview',
    'rename_failed': 'Error: Failed to rename file',
    'split_failed': 'Error: Failed to split file',
    'merge_failed': 'Error: Failed to merge files',
    'convert_failed': 'Error: Failed to convert file',
    'invalid_format': 'Error: Invalid file format',
    'no_parts': 'Error: No file parts found',
    'invalid_schedule': 'Error: Invalid schedule format'
}

# Progress Bar Configuration
PROGRESS_BAR_LENGTH = 20
PROGRESS_UPDATE_INTERVAL = 1  # seconds

# User Settings Defaults
DEFAULT_SETTINGS = {
    'notify_on_complete': True,
    'auto_delete_after_upload': True,
    'show_progress': True,
    'max_concurrent_uploads': 3,
    'default_hosting_service': 'gofile',
    'auto_compress': False,
    'compress_quality': 'medium',
    'generate_preview': True,
    'preview_size': 'medium',
    'auto_rename': False,
    'rename_pattern': '{original_name}_{timestamp}',
    'schedule_uploads': False,
    'timezone': 'UTC',
    'auto_split': False,
    'split_size': 100 * 1024 * 1024,  # 100MB
    'auto_convert': False,
    'convert_format': 'mp4',
    'keep_original': True,
    'max_retries': 3,
    'retry_delay': 5,  # seconds
    'chunk_size': 8192,  # bytes
    'temp_dir': 'temp',
    'preview_dir': 'previews',
    'log_level': 'INFO'
}

# Compression Settings
COMPRESSION_SETTINGS = {
    'low': {
        'quality': 60,
        'max_size': 1024 * 1024 * 10,  # 10MB
        'video_bitrate': '1000k',
        'audio_bitrate': '128k'
    },
    'medium': {
        'quality': 80,
        'max_size': 1024 * 1024 * 20,  # 20MB
        'video_bitrate': '2000k',
        'audio_bitrate': '192k'
    },
    'high': {
        'quality': 90,
        'max_size': 1024 * 1024 * 50,  # 50MB
        'video_bitrate': '4000k',
        'audio_bitrate': '256k'
    }
}

# Preview Settings
PREVIEW_SETTINGS = {
    'small': {
        'width': 320,
        'height': 240,
        'format': 'jpeg',
        'quality': 80
    },
    'medium': {
        'width': 640,
        'height': 480,
        'format': 'jpeg',
        'quality': 85
    },
    'large': {
        'width': 1280,
        'height': 720,
        'format': 'jpeg',
        'quality': 90
    }
}

# File Format Conversion Settings
CONVERSION_SETTINGS = {
    'video': {
        'mp4': {
            'codec': 'libx264',
            'audio_codec': 'aac',
            'container': 'mp4'
        },
        'webm': {
            'codec': 'libvpx',
            'audio_codec': 'libopus',
            'container': 'webm'
        },
        'mkv': {
            'codec': 'libx264',
            'audio_codec': 'aac',
            'container': 'mkv'
        }
    },
    'audio': {
        'mp3': {
            'codec': 'libmp3lame',
            'container': 'mp3'
        },
        'ogg': {
            'codec': 'libvorbis',
            'container': 'ogg'
        },
        'm4a': {
            'codec': 'aac',
            'container': 'm4a'
        }
    },
    'image': {
        'jpg': {
            'format': 'jpeg',
            'quality': 85
        },
        'png': {
            'format': 'png',
            'optimize': True
        },
        'webp': {
            'format': 'webp',
            'quality': 85
        }
    }
}

# Schedule Format
SCHEDULE_FORMAT = "%Y-%m-%d %H:%M:%S"

# File Naming Patterns
FILENAME_PATTERNS = {
    'default': '{original_name}_{timestamp}',
    'date': '{original_name}_{date}',
    'time': '{original_name}_{time}',
    'datetime': '{original_name}_{datetime}',
    'random': '{original_name}_{random}',
    'custom': '{original_name}_{custom}'
}

# Logging Configuration
LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'standard',
            'level': 'INFO'
        },
        'file': {
            'class': 'logging.FileHandler',
            'formatter': 'standard',
            'filename': 'bot.log',
            'level': 'INFO'
        }
    },
    'loggers': {
        '': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': True
        }
    }
}

# Monitor settings
MONITOR_SETTINGS = {
    'cooldown_period': 5,  # seconds to wait before processing a file
    'min_file_size': 1024,  # 1KB minimum file size
    'max_file_size': 1024 * 1024 * 1024,  # 1GB maximum file size
    'watch_recursive': True,  # watch subdirectories by default
    'auto_upload': False,  # automatically upload files when detected
    'excluded_paths': [],  # paths to exclude from monitoring
    'included_paths': [],  # paths to include in monitoring
    'file_patterns': ['*'],  # file patterns to watch
    'excluded_patterns': [],  # file patterns to exclude
} 
