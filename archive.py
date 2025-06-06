import os
import zipfile
import tarfile
import gzip
import bz2
import lzma
import logging
from typing import List, Optional, Dict, Union
from datetime import datetime

logger = logging.getLogger(__name__)

class FileArchiver:
    def __init__(self):
        """Initialize FileArchiver with supported compression methods."""
        self.supported_formats = {
            'zip': self._create_zip,
            'tar': self._create_tar,
            'tar.gz': self._create_targz,
            'tar.bz2': self._create_tarbz2,
            'tar.xz': self._create_tarxz,
            'gz': self._create_gzip,
            'bz2': self._create_bzip2,
            'xz': self._create_lzma
        }

    def archive_files(self, 
                     files: List[str], 
                     output_path: str, 
                     format: str = 'zip',
                     compression_level: int = 6,
                     password: Optional[str] = None) -> Dict:
        """Archive multiple files into a single archive."""
        try:
            if format not in self.supported_formats:
                raise ValueError(f"Unsupported archive format: {format}")

            # Validate input files
            for file_path in files:
                if not os.path.exists(file_path):
                    raise FileNotFoundError(f"File not found: {file_path}")

            # Create archive
            archive_path = self.supported_formats[format](
                files, 
                output_path, 
                compression_level,
                password
            )

            # Generate metadata
            metadata = {
                'archive_path': archive_path,
                'format': format,
                'compression_level': compression_level,
                'is_encrypted': bool(password),
                'file_count': len(files),
                'total_size': os.path.getsize(archive_path),
                'created_at': datetime.now().isoformat(),
                'files': [os.path.basename(f) for f in files]
            }

            return metadata

        except Exception as e:
            logger.error(f"Error creating archive: {str(e)}")
            raise

    def _create_zip(self, 
                   files: List[str], 
                   output_path: str,
                   compression_level: int,
                   password: Optional[str] = None) -> str:
        """Create a ZIP archive."""
        try:
            if not output_path.endswith('.zip'):
                output_path += '.zip'

            with zipfile.ZipFile(
                output_path,
                'w',
                compression=zipfile.ZIP_DEFLATED,
                compresslevel=compression_level
            ) as zipf:
                for file_path in files:
                    arcname = os.path.basename(file_path)
                    if password:
                        zipf.setpassword(password.encode())
                    zipf.write(file_path, arcname)

            return output_path

        except Exception as e:
            logger.error(f"Error creating ZIP archive: {str(e)}")
            raise

    def _create_tar(self, 
                   files: List[str], 
                   output_path: str,
                   compression_level: int,
                   password: Optional[str] = None) -> str:
        """Create a TAR archive."""
        try:
            if not output_path.endswith('.tar'):
                output_path += '.tar'

            with tarfile.open(output_path, 'w') as tar:
                for file_path in files:
                    tar.add(file_path, os.path.basename(file_path))

            return output_path

        except Exception as e:
            logger.error(f"Error creating TAR archive: {str(e)}")
            raise

    def _create_targz(self, 
                     files: List[str], 
                     output_path: str,
                     compression_level: int,
                     password: Optional[str] = None) -> str:
        """Create a TAR.GZ archive."""
        try:
            if not output_path.endswith('.tar.gz'):
                output_path += '.tar.gz'

            with tarfile.open(output_path, 'w:gz', compresslevel=compression_level) as tar:
                for file_path in files:
                    tar.add(file_path, os.path.basename(file_path))

            return output_path

        except Exception as e:
            logger.error(f"Error creating TAR.GZ archive: {str(e)}")
            raise

    def _create_tarbz2(self, 
                      files: List[str], 
                      output_path: str,
                      compression_level: int,
                      password: Optional[str] = None) -> str:
        """Create a TAR.BZ2 archive."""
        try:
            if not output_path.endswith('.tar.bz2'):
                output_path += '.tar.bz2'

            with tarfile.open(output_path, 'w:bz2', compresslevel=compression_level) as tar:
                for file_path in files:
                    tar.add(file_path, os.path.basename(file_path))

            return output_path

        except Exception as e:
            logger.error(f"Error creating TAR.BZ2 archive: {str(e)}")
            raise

    def _create_tarxz(self, 
                     files: List[str], 
                     output_path: str,
                     compression_level: int,
                     password: Optional[str] = None) -> str:
        """Create a TAR.XZ archive."""
        try:
            if not output_path.endswith('.tar.xz'):
                output_path += '.tar.xz'

            with tarfile.open(output_path, 'w:xz', preset=compression_level) as tar:
                for file_path in files:
                    tar.add(file_path, os.path.basename(file_path))

            return output_path

        except Exception as e:
            logger.error(f"Error creating TAR.XZ archive: {str(e)}")
            raise

    def _create_gzip(self, 
                    files: List[str], 
                    output_path: str,
                    compression_level: int,
                    password: Optional[str] = None) -> str:
        """Create a GZIP archive."""
        try:
            if len(files) > 1:
                raise ValueError("GZIP format only supports single file compression")

            if not output_path.endswith('.gz'):
                output_path += '.gz'

            with open(files[0], 'rb') as f_in:
                with gzip.open(output_path, 'wb', compresslevel=compression_level) as f_out:
                    f_out.writelines(f_in)

            return output_path

        except Exception as e:
            logger.error(f"Error creating GZIP archive: {str(e)}")
            raise

    def _create_bzip2(self, 
                     files: List[str], 
                     output_path: str,
                     compression_level: int,
                     password: Optional[str] = None) -> str:
        """Create a BZIP2 archive."""
        try:
            if len(files) > 1:
                raise ValueError("BZIP2 format only supports single file compression")

            if not output_path.endswith('.bz2'):
                output_path += '.bz2'

            with open(files[0], 'rb') as f_in:
                with bz2.open(output_path, 'wb', compresslevel=compression_level) as f_out:
                    f_out.writelines(f_in)

            return output_path

        except Exception as e:
            logger.error(f"Error creating BZIP2 archive: {str(e)}")
            raise

    def _create_lzma(self, 
                    files: List[str], 
                    output_path: str,
                    compression_level: int,
                    password: Optional[str] = None) -> str:
        """Create a LZMA archive."""
        try:
            if len(files) > 1:
                raise ValueError("LZMA format only supports single file compression")

            if not output_path.endswith('.xz'):
                output_path += '.xz'

            with open(files[0], 'rb') as f_in:
                with lzma.open(output_path, 'wb', preset=compression_level) as f_out:
                    f_out.writelines(f_in)

            return output_path

        except Exception as e:
            logger.error(f"Error creating LZMA archive: {str(e)}")
            raise

    def extract_archive(self, 
                       archive_path: str, 
                       extract_path: str,
                       password: Optional[str] = None) -> Dict:
        """Extract an archive to the specified path."""
        try:
            if not os.path.exists(archive_path):
                raise FileNotFoundError(f"Archive not found: {archive_path}")

            # Create extract directory if it doesn't exist
            os.makedirs(extract_path, exist_ok=True)

            # Determine archive format
            format = self._get_archive_format(archive_path)
            if format not in self.supported_formats:
                raise ValueError(f"Unsupported archive format: {format}")

            # Extract archive
            if format == 'zip':
                with zipfile.ZipFile(archive_path, 'r') as zipf:
                    if password:
                        zipf.setpassword(password.encode())
                    zipf.extractall(extract_path)
            else:
                with tarfile.open(archive_path, 'r:*') as tar:
                    tar.extractall(extract_path)

            # Generate metadata
            metadata = {
                'archive_path': archive_path,
                'format': format,
                'extract_path': extract_path,
                'extracted_at': datetime.now().isoformat(),
                'is_encrypted': bool(password)
            }

            return metadata

        except Exception as e:
            logger.error(f"Error extracting archive: {str(e)}")
            raise

    def _get_archive_format(self, archive_path: str) -> str:
        """Determine the format of an archive file."""
        try:
            if archive_path.endswith('.zip'):
                return 'zip'
            elif archive_path.endswith('.tar'):
                return 'tar'
            elif archive_path.endswith('.tar.gz'):
                return 'tar.gz'
            elif archive_path.endswith('.tar.bz2'):
                return 'tar.bz2'
            elif archive_path.endswith('.tar.xz'):
                return 'tar.xz'
            elif archive_path.endswith('.gz'):
                return 'gz'
            elif archive_path.endswith('.bz2'):
                return 'bz2'
            elif archive_path.endswith('.xz'):
                return 'xz'
            else:
                raise ValueError(f"Unknown archive format: {archive_path}")
        except Exception as e:
            logger.error(f"Error determining archive format: {str(e)}")
            raise 