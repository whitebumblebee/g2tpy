import os
import shutil
import subprocess
import logging
from pathlib import Path
import mimetypes
from urllib.parse import urlparse


def normalize_github_url(url):
    """Normalizes various GitHub URL formats to a consistent format."""
    try:
        # Remove trailing slashes
        url = url.rstrip('/')

        # Handle git@ URLs
        if url.startswith('git@github.com:'):
            return url

        # Handle full HTTPS URLs
        if url.startswith('https://github.com/'):
            return url

        # Handle short format (user/repo)
        parts = url.split('/')
        if len(parts) == 2:
            return f"https://github.com/{url}"

        raise ValueError('Invalid GitHub repository URL format')
    except ValueError as e:
        raise ValueError(f"Invalid GitHub URL: {url}") from e


def download_repository(repo_url, temp_dir):
    """Downloads a GitHub repository to a temporary directory."""
    try:
        normalized_url = normalize_github_url(repo_url)

        logging.info(f"Downloading repository from {normalized_url} to {temp_dir}")

        # Clone the repository using git
        subprocess.run(["git", "clone", "--depth", "1", normalized_url, temp_dir], check=True, capture_output=True)

        # Verify the download
        if not os.listdir(temp_dir):
            raise Exception("Repository appears to be empty")

        logging.info("Repository downloaded successfully.")
    except subprocess.CalledProcessError as e:
        logging.error(f"Git clone failed. Output:\n{e.stderr.decode()}")
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise Exception("Failed to download repository.") from e


def is_text_file(filepath):
    """Determine if a file is text or binary based on its content type."""
    mime_type, _ = mimetypes.guess_type(filepath)
    if mime_type is None:
      # If mime type is unknown assume it's text based on the extension.  This is not perfect.
      ext = Path(filepath).suffix.lower()
      text_extensions = ['.txt', '.js', '.py', '.html', '.css', '.md', '.json', '.xml', '.yaml', '.yml', '.c', '.cpp', '.h', '.hpp', '.java', '.go', '.sh', '.rb', '.php']  # common text extensions.
      return ext in text_extensions

    return mime_type.startswith('text/')


def process_files(repo_dir, output_file, threshold_mb, include_all):
    """Processes files in the repository directory and combines them into a single text output."""
    threshold_bytes = threshold_mb * 1024 * 1024
    total_processed_files = 0
    total_skipped_files = 0

    try:
        with open(output_file, "w", encoding="utf-8") as outfile:
            for root, dirs, files in os.walk(repo_dir):

                # Skip node_modules directories
                if "node_modules" in root:
                    continue
                
                for filename in files:
                    filepath = os.path.join(root, filename)
                    
                    try:
                        file_size = os.path.getsize(filepath)

                        # Skip if file is too large and include_all is False
                        if not include_all and file_size > threshold_bytes:
                            logging.debug(f"Skipping large file: {filename}")
                            total_skipped_files += 1
                            continue

                        # Skip binary files unless includeAll is true
                        if not include_all and not is_text_file(filepath):
                            logging.debug(f"Skipping binary file: {filename}")
                            total_skipped_files += 1
                            continue

                        try:
                            with open(filepath, "r", encoding="utf-8") as infile:
                                content = infile.read()
                        except UnicodeDecodeError:  # Handle files that are not valid UTF-8
                            logging.warning(f"Skipping file due to UTF-8 decode error: {filename}")
                            total_skipped_files += 1
                            continue

                        relative_path = os.path.relpath(filepath, repo_dir)

                        outfile.write("=" * 80 + "\n")
                        outfile.write(f"File: {relative_path}\n")
                        outfile.write(f"Size: {file_size / 1024:.2f} KB\n")
                        outfile.write("=" * 80 + "\n\n")
                        outfile.write(content + "\n")

                        total_processed_files += 1
                        logging.debug(f"Processed file: {relative_path}")

                    except Exception as e:
                        logging.error(f"Error processing {filename}: {e}")
                        total_skipped_files += 1

        logging.info(f"Processed {total_processed_files} files successfully ({total_skipped_files} skipped)")

    except Exception as e:
        logging.error(f"Failed to process files: {e}")
        raise