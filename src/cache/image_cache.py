"""
Image caching system for downloaded images
"""
import os
import hashlib
import time
from pathlib import Path
from PIL import Image


class ImageCache:
    def __init__(self, cache_dir='data/images'):
        """Initialize image cache"""
        # Convert to absolute path
        if not os.path.isabs(cache_dir):
            # Get the project root directory
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            cache_dir = os.path.join(project_root, cache_dir)

        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)
        print(f"Image cache initialized at: {self.cache_dir}")
    
    def _get_cache_filename(self, url, item_type=None):
        """Generate cache filename from URL with optional category subdirectory"""
        # Use MD5 hash of URL as filename
        url_hash = hashlib.md5(url.encode()).hexdigest()
        
        # Try to preserve file extension
        ext = '.jpg'
        if url:
            for e in ['.png', '.jpg', '.jpeg', '.webp', '.gif']:
                if e in url.lower():
                    ext = e
                    break
        
        filename = f"{url_hash}{ext}"
        
        # Add category subdirectory if provided
        if item_type:
            # Sanitize item_type for use as directory name
            safe_type = item_type.replace('/', '_').replace('\\', '_').replace(' ', '_')
            return os.path.join(safe_type, filename)
        
        return filename
    
    def get_cached_path(self, url, item_type=None):
        """Get path to cached image if it exists"""
        if not url:
            return None
        
        filename = self._get_cache_filename(url, item_type)
        filepath = os.path.join(self.cache_dir, filename)
        
        if os.path.exists(filepath):
            return filepath
        
        return None
    
    def save_image(self, url, image_data_or_path, item_type=None):
        """Save image to cache with optional category subdirectory and generate thumbnails"""
        try:
            filename = self._get_cache_filename(url, item_type)
            filepath = os.path.join(self.cache_dir, filename)
            
            # Create subdirectory if needed
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            # If it's a path, copy the file
            if isinstance(image_data_or_path, (str, Path)) and os.path.exists(image_data_or_path):
                img = Image.open(image_data_or_path)
                # Save original
                img.save(filepath)
                # Generate thumbnails
                self._generate_thumbnails(img, filepath)
            # If it's bytes, save directly
            elif isinstance(image_data_or_path, bytes):
                with open(filepath, 'wb') as f:
                    f.write(image_data_or_path)
                # Open and generate thumbnails
                img = Image.open(filepath)
                self._generate_thumbnails(img, filepath)
            else:
                return None
            
            return filepath
        
        except Exception as e:
            print(f"Error saving image to cache: {e}")
            return None
    
    def _generate_thumbnails(self, img, original_path):
        """Generate thumbnail versions of an image"""
        try:
            # Get base path without extension
            base_path = os.path.splitext(original_path)[0]
            
            # Thumbnail (64x64) - for grid/search
            thumb_img = img.copy()
            thumb_img.thumbnail((64, 64), Image.Resampling.LANCZOS)
            thumb_path = f"{base_path}_thumb.png"
            thumb_img.save(thumb_path, 'PNG', optimize=True)
            
            # Medium (256x256) - for modal preview
            medium_img = img.copy()
            medium_img.thumbnail((256, 256), Image.Resampling.LANCZOS)
            medium_path = f"{base_path}_medium.png"
            medium_img.save(medium_path, 'PNG', optimize=True)
            
            return True
        except Exception as e:
            print(f"Error generating thumbnails: {e}")
            return False
    
    def get_thumbnail_path(self, url, item_type=None):
        """Get path to thumbnail version of cached image"""
        filepath = self.get_cached_path(url, item_type)
        if filepath:
            base_path = os.path.splitext(filepath)[0]
            thumb_path = f"{base_path}_thumb.png"
            if os.path.exists(thumb_path):
                return thumb_path
        return None
    
    def get_medium_path(self, url, item_type=None):
        """Get path to medium version of cached image"""
        filepath = self.get_cached_path(url, item_type)
        if filepath:
            base_path = os.path.splitext(filepath)[0]
            medium_path = f"{base_path}_medium.png"
            if os.path.exists(medium_path):
                return medium_path
        return None
    
    def clear_cache(self):
        """Clear all cached images including subdirectories"""
        try:
            import shutil
            for item in os.listdir(self.cache_dir):
                if item == '.gitkeep':
                    continue
                itempath = os.path.join(self.cache_dir, item)
                if os.path.isfile(itempath):
                    os.remove(itempath)
                elif os.path.isdir(itempath):
                    shutil.rmtree(itempath)
            return True
        except Exception as e:
            print(f"Error clearing cache: {e}")
            return False
    
    def get_cache_size(self):
        """Get total size of cache in bytes including subdirectories"""
        total_size = 0
        for root, dirs, files in os.walk(self.cache_dir):
            for file in files:
                if file == '.gitkeep':
                    continue
                filepath = os.path.join(root, file)
                if os.path.isfile(filepath):
                    total_size += os.path.getsize(filepath)
        return total_size

    def get_cache_stats(self):
        """Get cache statistics (size, file count)"""
        total_size = 0
        file_count = 0
        for root, dirs, files in os.walk(self.cache_dir):
            for file in files:
                if file == '.gitkeep':
                    continue
                filepath = os.path.join(root, file)
                if os.path.isfile(filepath):
                    total_size += os.path.getsize(filepath)
                    file_count += 1
        return {
            'size_bytes': total_size,
            'size_mb': round(total_size / (1024 * 1024), 2),
            'file_count': file_count
        }

    def get_orphaned_images(self, db_connection):
        """
        Find images in cache that are not referenced in database

        Args:
            db_connection: Database connection to query image_path references

        Returns:
            List of file paths that are orphaned
        """
        orphaned = []

        try:
            # Get all image_path values from database
            cursor = db_connection.cursor()
            cursor.execute("SELECT image_path FROM items WHERE image_path IS NOT NULL")
            db_paths = set(row[0] for row in cursor.fetchall())

            # Walk through cache directory
            for root, dirs, files in os.walk(self.cache_dir):
                for file in files:
                    if file == '.gitkeep':
                        continue

                    filepath = os.path.join(root, file)

                    # Check if this file is referenced in database
                    if filepath not in db_paths:
                        orphaned.append(filepath)

            return orphaned

        except Exception as e:
            print(f"Error finding orphaned images: {e}")
            return []

    def cleanup_orphaned_images(self, db_connection):
        """
        Remove images from cache that are not referenced in database

        Args:
            db_connection: Database connection to query image_path references

        Returns:
            Dict with cleanup statistics
        """
        orphaned = self.get_orphaned_images(db_connection)

        removed_count = 0
        freed_bytes = 0
        errors = []

        for filepath in orphaned:
            try:
                file_size = os.path.getsize(filepath)
                os.remove(filepath)
                removed_count += 1
                freed_bytes += file_size
            except Exception as e:
                errors.append({'file': filepath, 'error': str(e)})

        return {
            'removed_count': removed_count,
            'freed_mb': round(freed_bytes / (1024 * 1024), 2),
            'errors': errors
        }

    def cleanup_old_images(self, max_age_days=30):
        """
        Remove images older than max_age_days

        Args:
            max_age_days: Maximum age in days before image is considered old

        Returns:
            Dict with cleanup statistics
        """
        max_age_seconds = max_age_days * 24 * 60 * 60
        current_time = time.time()

        removed_count = 0
        freed_bytes = 0
        errors = []

        for root, dirs, files in os.walk(self.cache_dir):
            for file in files:
                if file == '.gitkeep':
                    continue

                filepath = os.path.join(root, file)

                try:
                    # Get file modification time
                    file_mtime = os.path.getmtime(filepath)
                    file_age = current_time - file_mtime

                    if file_age > max_age_seconds:
                        file_size = os.path.getsize(filepath)
                        os.remove(filepath)
                        removed_count += 1
                        freed_bytes += file_size

                except Exception as e:
                    errors.append({'file': filepath, 'error': str(e)})

        return {
            'removed_count': removed_count,
            'freed_mb': round(freed_bytes / (1024 * 1024), 2),
            'errors': errors
        }

    def cleanup_by_size(self, max_size_mb=1000):
        """
        Remove least recently used images until cache is under max_size_mb
        Uses LRU strategy (Least Recently Used)

        Args:
            max_size_mb: Maximum cache size in megabytes

        Returns:
            Dict with cleanup statistics
        """
        max_size_bytes = max_size_mb * 1024 * 1024
        current_size = self.get_cache_size()

        if current_size <= max_size_bytes:
            return {
                'removed_count': 0,
                'freed_mb': 0,
                'message': 'Cache size already under limit'
            }

        # Get all files with their access times
        files_with_atime = []

        for root, dirs, files in os.walk(self.cache_dir):
            for file in files:
                if file == '.gitkeep':
                    continue

                filepath = os.path.join(root, file)

                try:
                    stat_info = os.stat(filepath)
                    files_with_atime.append({
                        'path': filepath,
                        'atime': stat_info.st_atime,  # Last access time
                        'size': stat_info.st_size
                    })
                except Exception:
                    continue

        # Sort by access time (oldest first)
        files_with_atime.sort(key=lambda x: x['atime'])

        removed_count = 0
        freed_bytes = 0
        errors = []

        # Remove oldest files until we're under the limit
        for file_info in files_with_atime:
            if current_size <= max_size_bytes:
                break

            try:
                os.remove(file_info['path'])
                removed_count += 1
                freed_bytes += file_info['size']
                current_size -= file_info['size']
            except Exception as e:
                errors.append({'file': file_info['path'], 'error': str(e)})

        return {
            'removed_count': removed_count,
            'freed_mb': round(freed_bytes / (1024 * 1024), 2),
            'errors': errors
        }
