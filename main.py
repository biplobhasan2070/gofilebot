import os
import logging
import asyncio
import uuid
from typing import Optional, Tuple, Dict
from datetime import datetime
from pyrogram import Client, filters
from pyrogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton, Message,
    CallbackQuery, User
)
from pyrogram.errors import FloodWait
from gofile import uploadFile, GoFileError, GoFileAPIError, GoFileUploadError, parse_upload_command
from config import (
    BOT_TOKEN, API_ID, API_HASH, INSTRUCTIONS, ERROR_MESSAGES,
    MAX_FILE_SIZE, ALLOWED_EXTENSIONS, BOT_COMMANDS,
    PROGRESS_BAR_LENGTH, PROGRESS_UPDATE_INTERVAL
)
from database import (
    get_active_operations, add_operation, remove_operation,
    update_operation_status, get_stats, update_stats,
    get_user_settings, update_user_settings
)
import aiohttp
from aiohttp import ClientTimeout
import requests

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize bot
Bot = Client(
    "GoFile-Bot",
    bot_token=BOT_TOKEN,
    api_id=API_ID,
    api_hash=API_HASH
)

# Active operations tracking
active_operations: Dict[str, Dict] = {}

def format_size(size: int) -> str:
    """Format size in bytes to human readable format."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024:
            return f"{size:.2f} {unit}"
        size /= 1024
    return f"{size:.2f} TB"

def create_progress_bar(progress: float) -> str:
    """Create a progress bar string."""
    filled_length = int(PROGRESS_BAR_LENGTH * progress)
    bar = '█' * filled_length + '░' * (PROGRESS_BAR_LENGTH - filled_length)
    return f"[{bar}] {progress:.1%}"

def validate_file_size(file_path: str) -> bool:
    """Validate if file size is within limits."""
    try:
        return os.path.getsize(file_path) <= MAX_FILE_SIZE
    except Exception:
        return False

def validate_file_type(file_path: str) -> bool:
    """Validate if file type is allowed."""
    try:
        ext = os.path.splitext(file_path)[1].lower().lstrip('.')
        # Check if extension is in any of the allowed categories
        return any(ext in exts for exts in ALLOWED_EXTENSIONS.values())
    except Exception as e:
        logger.error(f"Error validating file type: {str(e)}")
        return False

async def update_progress_message(
    current: int,
    total: int,
    message: Message,
    status: str,
    file_name: str,
    operation_id: str,
    *args
):
    """Update progress message with current status."""
    if not isinstance(message, Message):
        logger.error("Invalid message object")
        return
    progress = current / total if total else 0
    progress_bar = create_progress_bar(progress)
    text = f"**{status}**\n\n"
    text += f"**File:** `{file_name}`\n"
    text += f"**Size:** {format_size(total)}\n"
    text += f"**Progress:** {progress_bar}\n\n"
    text += "Click the button below to cancel the operation."
    
    reply_markup = InlineKeyboardMarkup([[
        InlineKeyboardButton(
            "❌ Cancel",
            callback_data=f"cancel_{operation_id}"
        )
    ]])
    
    try:
        await message.edit_text(text, reply_markup=reply_markup)
    except FloodWait as e:
        await asyncio.sleep(e.value)
    except Exception as e:
        logger.error(f"Failed to update progress message: {str(e)}")

async def download_with_progress(
    message: Message,
    file_name: str,
    operation_id: str,
    url: str = None,
    reply_message: Message = None
) -> str:
    """Download file with progress tracking and immediate cancellation support."""
    if url:
        timeout = ClientTimeout(total=None)  # No timeout
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url) as response:
                if response.status != 200:
                    raise ValueError(f"Failed to download: HTTP {response.status}")
                
                total_size = int(response.headers.get('content-length', 0))
                media = url.split("/")[-1]
                
                downloaded = 0
                with open(media, "wb") as file:
                    async for chunk in response.content.iter_chunked(8192):
                        if active_operations[operation_id]['cancelled']:
                            file.close()
                            if os.path.exists(media):
                                os.remove(media)
                            raise ValueError(ERROR_MESSAGES['operation_cancelled'])
                        
                        file.write(chunk)
                        downloaded += len(chunk)
                        progress = downloaded / total_size
                        await update_progress_message(
                            downloaded,
                            total_size,
                            message,
                            "Downloading",
                            media,
                            operation_id
                        )
    else:
        if not reply_message:
            raise ValueError("No message to download from")
        
        # Create a task for the download
        download_task = asyncio.create_task(
            reply_message.download(
                progress=update_progress_message,
                progress_args=(message, "Downloading", file_name, operation_id)
            )
        )
        
        # Wait for either download completion or cancellation
        while not download_task.done():
            if active_operations[operation_id]['cancelled']:
                download_task.cancel()
                try:
                    await download_task
                except asyncio.CancelledError:
                    pass
                raise ValueError(ERROR_MESSAGES['operation_cancelled'])
            await asyncio.sleep(0.1)
        
        try:
            media = await download_task
        except Exception as e:
            if active_operations[operation_id]['cancelled']:
                raise ValueError(ERROR_MESSAGES['operation_cancelled'])
            raise e
            
    return media

@Bot.on_callback_query(filters.regex("^cancel_"))
async def handle_cancel(client: Client, callback_query: CallbackQuery):
    """Handle cancel button callback with immediate cancellation."""
    operation_id = callback_query.data.split("_")[1]
    if operation_id in active_operations:
        active_operations[operation_id]['cancelled'] = True
        await callback_query.answer("Operation cancelled")
        await callback_query.message.edit_text(
            ERROR_MESSAGES['operation_cancelled'],
            reply_markup=None
        )
    else:
        await callback_query.answer(ERROR_MESSAGES['no_active_operation'])

@Bot.on_message(filters.private & filters.command("start"))
async def start(bot: Client, update: Message):
    """Handle /start command."""
    # Set bot commands
    await bot.set_bot_commands(BOT_COMMANDS)
    
    await update.reply_text(
        text=f"Hello {update.from_user.mention}," + INSTRUCTIONS,
        disable_web_page_preview=True,
        quote=True
    )

@Bot.on_message(filters.private & filters.command("help"))
async def help_command(bot: Client, update: Message):
    """Handle /help command."""
    await update.reply_text(
        text=INSTRUCTIONS,
        disable_web_page_preview=True,
        quote=True
    )

@Bot.on_message(filters.private & filters.command("status"))
async def status_command(bot: Client, update: Message):
    """Handle /status command."""
    user_id = update.from_user.id
    active_ops = get_active_operations(user_id)
    
    if not active_ops:
        await update.reply_text("No active operations")
        return
    
    text = "**Active Operations:**\n\n"
    for op in active_ops:
        text += f"**Operation:** {op['type']}\n"
        text += f"**Started:** {op['start_time']}\n"
        text += f"**Status:** {op['status']}\n\n"
    
    await update.reply_text(text)

@Bot.on_message(filters.private & filters.command("stats"))
async def stats_command(bot: Client, update: Message):
    """Handle /stats command."""
    user_id = update.from_user.id
    user_stats = get_stats(user_id)
    global_stats = get_stats()
    
    text = "**Your Statistics:**\n\n"
    text += f"**Total Uploads:** {user_stats['uploads']}\n"
    text += f"**Total Size:** {format_size(user_stats['total_size'])}\n"
    if user_stats['last_upload']:
        text += f"**Last Upload:** {user_stats['last_upload']}\n\n"
    
    text += "**Global Statistics:**\n\n"
    text += f"**Total Uploads:** {global_stats['total_uploads']}\n"
    text += f"**Total Size:** {format_size(global_stats['total_size'])}\n"
    text += f"**Bot Uptime:** {datetime.fromisoformat(global_stats['start_time']).strftime('%Y-%m-%d %H:%M:%S')}"
    
    await update.reply_text(text)

@Bot.on_message(filters.private & filters.command("settings"))
async def settings_command(bot: Client, update: Message):
    """Handle /settings command."""
    user_id = update.from_user.id
    settings = get_user_settings(user_id)
    
    text = "**Your Settings:**\n\n"
    for key, value in settings.items():
        if key != 'user_id':  # Don't show user_id in settings
            text += f"**{key}:** {value}\n"
    
    reply_markup = InlineKeyboardMarkup([[
        InlineKeyboardButton("⚙️ Edit Settings", callback_data="edit_settings")
    ]])
    
    await update.reply_text(text, reply_markup=reply_markup)

@Bot.on_message(filters.private & filters.command("about"))
async def about_command(bot: Client, update: Message):
    """Handle /about command."""
    text = "**GoFile Bot**\n\n"
    text += "A powerful Telegram bot for uploading files to GoFile.io\n\n"
    text += "**Features:**\n"
    text += "• File upload to GoFile\n"
    text += "• Progress tracking\n"
    text += "• Multiple file support\n"
    text += "• User statistics\n"
    text += "• Customizable settings\n\n"
    text += "**Developer:** @FayasNoushad"
    
    await update.reply_text(text)

async def upload_with_progress(
    file_path: str,
    message: Message,
    operation_id: str,
    token: str = None,
    folderId: str = None
) -> dict:
    """Upload file with progress tracking."""
    try:
        # Start upload
        await update_progress_message(
            0,
            os.path.getsize(file_path),
            message,
            "Uploading",
            os.path.basename(file_path),
            operation_id
        )
        
        # Perform upload
        response = uploadFile(
            file_path=file_path,
            token=token,
            folderId=folderId
        )
        
        # Update progress to 100% on completion
        await update_progress_message(
            os.path.getsize(file_path),
            os.path.getsize(file_path),
            message,
            "Uploading",
            os.path.basename(file_path),
            operation_id
        )
        
        return response
    except Exception as e:
        logger.error(f"Upload failed: {str(e)}")
        raise

@Bot.on_message(filters.private & filters.command("upload"))
async def handle_upload(bot: Client, update: Message):
    """Handle /upload command."""
    operation_id = str(uuid.uuid4())
    active_operations[operation_id] = {
        'cancelled': False,
        'user_id': update.from_user.id
    }
    
    # Add operation to database
    add_operation(operation_id, update.from_user.id, "upload")
    
    message = await update.reply_text(
        text="`Processing...`",
        quote=True,
        disable_web_page_preview=True
    )

    try:
        url, token, folderId = parse_upload_command(update.text, update.reply_to_message)
        
        # Download file
        await message.edit_text("`Downloading...`")
        try:
            file_name = "file"
            if update.reply_to_message and update.reply_to_message.document:
                file_name = update.reply_to_message.document.file_name
                
            media = await download_with_progress(
                message=message,
                file_name=file_name,
                operation_id=operation_id,
                url=url,
                reply_message=update.reply_to_message
            )
            
            if active_operations[operation_id]['cancelled']:
                raise ValueError(ERROR_MESSAGES['operation_cancelled'])
                
        except ValueError as e:
            if str(e) == ERROR_MESSAGES['operation_cancelled']:
                raise
            raise ValueError(f"Download failed: {str(e)}")
            
        await message.edit_text("`Downloaded Successfully`")

        # Validate file
        if not validate_file_size(media):
            raise ValueError(ERROR_MESSAGES['file_too_large'])
        if not validate_file_type(media):
            raise ValueError(ERROR_MESSAGES['invalid_file_type'])

        # Upload file with progress
        await message.edit_text("`Uploading...`")
        try:
            response = await upload_with_progress(
                file_path=media,
                message=message,
                operation_id=operation_id,
                token=token,
                folderId=folderId
            )
            update_stats(update.from_user.id, os.path.getsize(media))
        except (GoFileError, GoFileAPIError, GoFileUploadError) as e:
            raise ValueError(f"Upload failed: {str(e)}")
            
        await message.edit_text("`Uploaded Successfully`")

        # Clean up
        try:
            os.remove(media)
        except Exception as e:
            logger.warning(f"Failed to remove temporary file {media}: {str(e)}")

        # Prepare response
        text = f"**File Name:** `{response['name']}`\n"
        text += f"**File ID:** `{response['id']}`\n"
        text += f"**Parent Folder Code:** `{response['parentFolderCode']}`\n"
        text += f"**Guest Token:** `{response['guestToken']}`\n"
        text += f"**md5:** `{response['md5']}`\n"
        text += f"**Download Page:** `{response['downloadPage']}`"
        
        link = response["downloadPage"]
        reply_markup = InlineKeyboardMarkup([
            [
                InlineKeyboardButton(text="Open Link", url=link),
                InlineKeyboardButton(
                    text="Share Link",
                    url=f"https://telegram.me/share/url?url={link}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="Feedback",
                    url="https://telegram.me/FayasNoushad"
                )
            ]
        ])
        
        await message.edit_text(
            text=text,
            reply_markup=reply_markup,
            disable_web_page_preview=True
        )

        # Update operation status on success
        update_operation_status(operation_id, "completed")

    except ValueError as e:
        await message.edit_text(str(e))
        # Update operation status on failure
        update_operation_status(operation_id, "failed")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        await message.edit_text(ERROR_MESSAGES['upload_failed'])
        # Update operation status on failure
        update_operation_status(operation_id, "failed")
    finally:
        if operation_id in active_operations:
            del active_operations[operation_id]
        # Remove operation from database
        remove_operation(operation_id)

@Bot.on_message(filters.private & filters.command("batch"))
async def handle_batch(bot: Client, update: Message):
    """Handle /batch command for uploading multiple Telegram files to GoFile."""
    operation_id = str(uuid.uuid4())
    active_operations[operation_id] = {
        'cancelled': False,
        'user_id': update.from_user.id
    }
    
    # Add operation to database
    add_operation(operation_id, update.from_user.id, "batch_upload")
    
    message = await update.reply_text(
        text="`Please send the files you want to upload. Send /done when finished.`",
        quote=True,
        disable_web_page_preview=True
    )
    
    # Store files to upload
    files_to_upload = []
    
    @Bot.on_message(filters.private & filters.document & filters.user(update.from_user.id))
    async def collect_files(bot: Client, msg: Message):
        if msg.document:
            files_to_upload.append(msg)
            await msg.reply_text(f"File added to batch: {msg.document.file_name}")
    
    @Bot.on_message(filters.private & filters.command("done") & filters.user(update.from_user.id))
    async def start_upload(bot: Client, msg: Message):
        if not files_to_upload:
            await msg.reply_text("No files added to batch. Please send some files first.")
            return
            
        total_files = len(files_to_upload)
        successful_uploads = 0
        failed_uploads = 0
        
        status_message = await msg.reply_text(
            "`Starting batch upload...`",
            quote=True
        )
        
        for index, file_msg in enumerate(files_to_upload, 1):
            if active_operations[operation_id]['cancelled']:
                raise ValueError(ERROR_MESSAGES['operation_cancelled'])
            
            try:
                # Update status
                status_text = f"**Batch Upload Progress**\n\n"
                status_text += f"**Total Files:** {total_files}\n"
                status_text += f"**Current File:** {index}/{total_files}\n"
                status_text += f"**Successful:** {successful_uploads}\n"
                status_text += f"**Failed:** {failed_uploads}\n\n"
                status_text += f"**Uploading:** {file_msg.document.file_name}\n"
                
                reply_markup = InlineKeyboardMarkup([[
                    InlineKeyboardButton(
                        "❌ Cancel",
                        callback_data=f"cancel_{operation_id}"
                    )
                ]])
                
                await status_message.edit_text(status_text, reply_markup=reply_markup)
                
                # Download file
                media = await download_with_progress(
                    message=status_message,
                    file_name=file_msg.document.file_name,
                    operation_id=operation_id,
                    reply_message=file_msg
                )
                
                # Upload to GoFile
                response = await upload_with_progress(
                    file_path=media,
                    message=status_message,
                    operation_id=operation_id
                )
                
                # Send upload result
                text = f"**File Uploaded Successfully**\n\n"
                text += f"**File Name:** `{response['name']}`\n"
                text += f"**File ID:** `{response['id']}`\n"
                text += f"**Download Page:** `{response['downloadPage']}`"
                
                link = response["downloadPage"]
                reply_markup = InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton(text="Open Link", url=link),
                        InlineKeyboardButton(
                            text="Share Link",
                            url=f"https://telegram.me/share/url?url={link}"
                        )
                    ]
                ])
                
                await file_msg.reply_text(
                    text=text,
                    reply_markup=reply_markup,
                    disable_web_page_preview=True
                )
                
                successful_uploads += 1
                
            except Exception as e:
                logger.error(f"Failed to upload {file_msg.document.file_name}: {str(e)}")
                await file_msg.reply_text(f"Failed to upload {file_msg.document.file_name}: {str(e)}")
                failed_uploads += 1
                continue
            finally:
                # Clean up downloaded file
                try:
                    if os.path.exists(media):
                        os.remove(media)
                except Exception as e:
                    logger.warning(f"Failed to remove temporary file {media}: {str(e)}")
        
        # Final status update
        status_text = f"**Batch Upload Complete**\n\n"
        status_text += f"**Total Files:** {total_files}\n"
        status_text += f"**Successful:** {successful_uploads}\n"
        status_text += f"**Failed:** {failed_uploads}"
        
        await status_message.edit_text(status_text, reply_markup=None)
        
        # Update operation status
        update_operation_status(operation_id, "completed")
        
        # Clean up
        if operation_id in active_operations:
            del active_operations[operation_id]
        remove_operation(operation_id)
        
        # Remove message handlers
        Bot.remove_handler(collect_files)
        Bot.remove_handler(start_upload)
    
    # Set timeout for collecting files
    try:
        await asyncio.sleep(300)  # 5 minutes timeout
        if not files_to_upload:
            await message.edit_text("No files were added within 5 minutes. Batch upload cancelled.")
            if operation_id in active_operations:
                del active_operations[operation_id]
            remove_operation(operation_id)
            Bot.remove_handler(collect_files)
            Bot.remove_handler(start_upload)
    except Exception as e:
        logger.error(f"Error in batch upload timeout: {str(e)}")
        if operation_id in active_operations:
            del active_operations[operation_id]
        remove_operation(operation_id)
        Bot.remove_handler(collect_files)
        Bot.remove_handler(start_upload)

@Bot.on_message(filters.private & filters.command("getid"))
async def handle_getid(bot: Client, update: Message):
    """Handle /getid command to extract file IDs from GoFile URLs."""
    try:
        # Get the URL from the command
        args = update.text.split()
        if len(args) != 2:
            await update.reply_text(
                "Please provide a GoFile URL. Example:\n"
                "/getid https://gofile.io/d/abc123"
            )
            return
            
        url = args[1]
        
        # Extract file ID from different URL formats
        file_id = None
        if "gofile.io/d/" in url:
            file_id = url.split("gofile.io/d/")[1].split("/")[0]
        elif "gofile.io/download/" in url:
            file_id = url.split("gofile.io/download/")[1].split("/")[0]
            
        if not file_id:
            await update.reply_text("Invalid GoFile URL format. Please provide a valid GoFile URL.")
            return
            
        # Get file information
        try:
            response = requests.get(f"https://api.gofile.io/getFileInfo?fileId={file_id}")
            response.raise_for_status()
            data = response.json()
            
            if data["status"] == "ok":
                file_info = data["data"]
                text = "**File Information:**\n\n"
                text += f"**File ID:** `{file_id}`\n"
                text += f"**File Name:** `{file_info.get('name', 'N/A')}`\n"
                text += f"**File Size:** `{format_size(file_info.get('size', 0))}`\n"
                text += f"**Download Link:** `https://gofile.io/d/{file_id}`\n"
                text += f"**Direct Download:** `https://gofile.io/download/{file_id}/{file_info.get('name', 'file')}`"
                
                await update.reply_text(text)
            else:
                await update.reply_text("Failed to get file information. The file might not exist or has been deleted.")
                
        except requests.exceptions.RequestException as e:
            await update.reply_text(f"Error getting file information: {str(e)}")
            
    except Exception as e:
        logger.error(f"Error in getid command: {str(e)}")
        await update.reply_text("An error occurred while processing your request.")

if __name__ == "__main__":
    logger.info("Bot is starting...")
    Bot.run()
