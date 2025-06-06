import os
from tinydb import TinyDB, Query
from datetime import datetime

# Ensure the data directory exists
os.makedirs('data', exist_ok=True)

# Initialize database
db = TinyDB('data/bot_database.json')
operations_table = db.table('operations')
stats_table = db.table('stats')
settings_table = db.table('settings')

def get_active_operations(user_id: int = None):
    """Get active operations for a user or all users."""
    Operation = Query()
    if user_id:
        return operations_table.search(Operation.user_id == user_id)
    return operations_table.all()

def add_operation(operation_id: str, user_id: int, operation_type: str):
    """Add a new operation to the database."""
    operations_table.insert({
        'operation_id': operation_id,
        'user_id': user_id,
        'type': operation_type,
        'start_time': datetime.now().isoformat(),
        'status': 'active'
    })

def remove_operation(operation_id: str):
    """Remove an operation from the database."""
    Operation = Query()
    operations_table.remove(Operation.operation_id == operation_id)

def update_operation_status(operation_id: str, status: str):
    """Update the status of an operation."""
    Operation = Query()
    operations_table.update(
        {'status': status},
        Operation.operation_id == operation_id
    )

def get_stats(user_id: int = None):
    """Get statistics for a user or all users."""
    Stats = Query()
    if user_id:
        user_stats = stats_table.get(Stats.user_id == user_id)
        if not user_stats:
            return {
                'uploads': 0,
                'total_size': 0,
                'last_upload': None
            }
        return user_stats
    else:
        all_stats = stats_table.all()
        return {
            'total_uploads': sum(stat.get('uploads', 0) for stat in all_stats),
            'total_size': sum(stat.get('total_size', 0) for stat in all_stats),
            'start_time': datetime.now().isoformat()
        }

def update_stats(user_id: int, file_size: int):
    """Update user statistics."""
    Stats = Query()
    user_stats = stats_table.get(Stats.user_id == user_id)
    
    if user_stats:
        stats_table.update({
            'uploads': user_stats.get('uploads', 0) + 1,
            'total_size': user_stats.get('total_size', 0) + file_size,
            'last_upload': datetime.now().isoformat()
        }, Stats.user_id == user_id)
    else:
        stats_table.insert({
            'user_id': user_id,
            'uploads': 1,
            'total_size': file_size,
            'last_upload': datetime.now().isoformat()
        })

def get_user_settings(user_id: int):
    """Get user settings."""
    Settings = Query()
    settings = settings_table.get(Settings.user_id == user_id)
    if not settings:
        return {
            'auto_compress': False,
            'auto_preview': False,
            'default_host': 'gofile',
            'file_naming': 'original'
        }
    return settings

def update_user_settings(user_id: int, settings: dict):
    """Update user settings."""
    Settings = Query()
    if settings_table.get(Settings.user_id == user_id):
        settings_table.update(settings, Settings.user_id == user_id)
    else:
        settings['user_id'] = user_id
        settings_table.insert(settings) 