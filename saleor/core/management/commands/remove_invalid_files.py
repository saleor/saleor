"""Remove files with invalid/dangerous MIME types from storage.

This command scans specific directories in storage for files with invalid
MIME types. By default, it runs in dry-run mode showing what would be deleted
without actually removing files.
"""

import os

from django.conf import settings
from django.core.files.storage import default_storage
from django.core.management.base import BaseCommand

from ....graphql.core.validators.file import detect_mime_type


class Command(BaseCommand):
    help = "Removes files with invalid/dangerous MIME types from storage."

    # Directories to scan for invalid files
    DIRECTORIES_TO_SCAN = [
        "file_upload/",  # Files uploaded via FileUpload mutation
        "digital_contents/",  # Files uploaded via DigitalContentCreate mutation
    ]

    def add_arguments(self, parser):
        parser.add_argument(
            "--apply",
            action="store_true",
            help=(
                "Apply the changes and delete invalid files. "
                "Without this flag, the command runs in dry-run mode."
            ),
        )

    def handle(self, **options):
        is_dry_run = not options.get("apply", False)

        if is_dry_run:
            self.stdout.write(
                self.style.WARNING(
                    "Running in DRY-RUN mode. No files will be deleted. "
                    "Use --apply to actually delete files."
                )
            )

        total_checked = 0
        total_invalid = 0

        for directory in self.DIRECTORIES_TO_SCAN:
            self.stdout.write(f"\nScanning directory: {directory}")
            checked, invalid = self._scan_directory(directory, is_dry_run)
            total_checked += checked
            total_invalid += invalid

        # Summary
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write(f"Total files checked: {total_checked}")
        self.stdout.write(
            self.style.ERROR(f"Total invalid files found: {total_invalid}")
        )

        if is_dry_run and total_invalid > 0:
            self.stdout.write(
                self.style.WARNING(
                    "\nReview the list of files above. "
                    "If it looks correct, rerun with --apply to delete them."
                )
            )
        elif total_invalid > 0:
            self.stdout.write(self.style.SUCCESS("\nInvalid files have been deleted."))
        else:
            self.stdout.write(self.style.SUCCESS("\nNo invalid files found."))

    def _scan_directory(self, directory, is_dry_run):
        """Scan a directory for files with invalid mime types."""
        checked = 0
        invalid = 0

        try:
            # List all files in the directory
            directories, files = default_storage.listdir(directory)
        except FileNotFoundError:
            self.stdout.write(self.style.WARNING(f"  Directory not found: {directory}"))
            return 0, 0

        # Process files in current directory
        for filename in files:
            file_path = os.path.join(directory, filename)
            checked += 1

            if self._is_invalid_file(file_path):
                invalid += 1
                self._handle_invalid_file(file_path, is_dry_run)

        # Recursively scan subdirectories
        for subdir in directories:
            subdir_path = os.path.join(directory, subdir)
            sub_checked, sub_invalid = self._scan_directory(subdir_path, is_dry_run)
            checked += sub_checked
            invalid += sub_invalid

        return checked, invalid

    def _is_invalid_file(self, file_path):
        """Check if file has invalid mime type by reading actual file content."""
        if not file_path:
            return False

        if not default_storage.exists(file_path):
            return False

        if self._has_no_extension(file_path):
            return True

        # verify file extension to prevent unnecessary file reads
        if not self._has_allowed_extension(file_path):
            return True

        return self._verify_file_content(file_path)

    def _has_no_extension(self, file_path):
        """Check if file has no extension."""
        _, ext = os.path.splitext(file_path)
        return not ext.lower()

    def _has_allowed_extension(self, file_path):
        """Check if file extension is in allowed list."""
        _, ext = os.path.splitext(file_path)
        ext = ext.lower()

        for _mime_type, extensions in settings.ALLOWED_MIME_TYPES.items():
            if ext in extensions:
                return True
        return False

    def _verify_file_content(self, file_path):
        """Verify file content matches allowed MIME types."""
        try:
            with default_storage.open(file_path, "rb") as file:
                try:
                    actual_mime_type = detect_mime_type(file)

                    if not self._is_mime_type_allowed(actual_mime_type):
                        self.stdout.write(
                            self.style.WARNING(
                                f"  File {file_path} has mime type {actual_mime_type} "
                                f"not in allowed list"
                            )
                        )
                        return True

                    if not self._extension_matches_mime_type(
                        file_path, actual_mime_type
                    ):
                        _, ext = os.path.splitext(file_path)
                        self.stdout.write(
                            self.style.WARNING(
                                f"  File {file_path} has extension {ext.lower()} but actual "
                                f"mime type is {actual_mime_type}"
                            )
                        )
                        return True

                    return False
                except Exception:
                    return True
        except Exception as e:
            self.stdout.write(
                self.style.WARNING(f"  Failed to read file {file_path}: {str(e)}")
            )
            return False

    def _is_mime_type_allowed(self, mime_type):
        """Check if MIME type is in allowed list."""
        return mime_type in settings.ALLOWED_MIME_TYPES

    def _extension_matches_mime_type(self, file_path, mime_type):
        """Check if file extension matches the detected MIME type."""
        _, ext = os.path.splitext(file_path)
        ext = ext.lower()
        expected_extensions = settings.ALLOWED_MIME_TYPES.get(mime_type, [])
        return ext in expected_extensions

    def _handle_invalid_file(self, file_path, is_dry_run):
        """Handle an invalid file - log or delete based on mode."""
        if is_dry_run:
            self.stdout.write(self.style.WARNING(f"  Would delete: {file_path}"))
        else:
            self.stdout.write(f"  Deleting: {file_path}")
            try:
                if default_storage.exists(file_path):
                    default_storage.delete(file_path)
                    self.stdout.write(self.style.SUCCESS("    ✓ Deleted successfully"))
                else:
                    self.stdout.write(self.style.WARNING("    ⚠ File does not exist"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"    ✗ Failed to delete: {str(e)}"))
