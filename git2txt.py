import os
import shutil
import argparse
import logging
from pathlib import Path
import mimetypes
from urllib.parse import urlparse

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def is_git_repository(repo_path):
    """Checks if the given path is a valid Git repository."""
    git_dir = os.path.join(repo_path, ".git")
    return os.path.exists(git_dir) and os.path.isdir(git_dir)

def process_files(repo_dir, output_file, threshold_mb, include_all):
    """Processes files in the repository directory and combines them into a single text output."""
    threshold_bytes = threshold_mb * 1024 * 1024
    total_processed_files = 0
    total_skipped_files = 0

    try:
        with open(output_file, "w", encoding="utf-8") as outfile:
            for root, dirs, files in os.walk(repo_dir):  # Get directories also
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

                        if not include_all and not is_text_file(filepath):
                            logging.debug(f"Skipping binary file: {filename}")
                            total_skipped_files += 1
                            continue

                        try:
                            with open(filepath, "r", encoding="utf-8") as infile:
                                content = infile.read()
                        except UnicodeDecodeError:  # Handle files that are not valid UTF-8
                            logging.warning(f"Skipping file due to UTF-8 decode error: {filename}")
                            total_skipped_files +=1
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


def is_text_file(filepath):
    """Determine if a file is text or binary based on its content type."""
    mime_type, _ = mimetypes.guess_type(filepath)
    if mime_type is None:
      # If mime type is unknown assume it's text based on the extension.  This is not perfect.
      ext = Path(filepath).suffix.lower()
      text_extensions = ['.txt', '.js', '.py', '.html', '.css', '.md', '.json', '.xml', '.yaml', '.yml', '.c', '.cpp', '.h', '.hpp', '.java', '.go', '.sh', '.rb', '.php']  # common text extensions.
      return ext in text_extensions

    return mime_type.startswith('text/')

def main():
    parser = argparse.ArgumentParser(description="Convert GitHub repositories (public or local clones) to text files.")
    group = parser.add_mutually_exclusive_group(required=True)  # one argument required, can't have both
    group.add_argument("repo_url", nargs='?', help="GitHub repository URL (for public repos).")
    group.add_argument("-l", "--local-path", dest="local_path", help="Path to a local cloned repository.", default=None)

    parser.add_argument("-o", "--output", help="Specify output file path", default=None)
    parser.add_argument("-t", "--threshold", type=float, help="Set file size threshold in MB", default=0.1)
    parser.add_argument("--include-all", action="store_true", help="Include all files regardless of size or type")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode with verbose logging")
    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)


    try:
        if args.local_path:
            repo_path = Path(args.local_path).resolve()  # ensure absolute path

            if not repo_path.exists() or not repo_path.is_dir():
                raise ValueError(f"Local path '{args.local_path}' does not exist or is not a directory.")

            if not is_git_repository(repo_path):
                raise ValueError(f"The directory '{args.local_path}' is not a valid Git repository. It must contain a .git folder.")

            # Extract repo name from the absolute path.  This could be improved.
            repo_name = repo_path.name
            if args.output:
                output_file = args.output
            else:
                output_file = f"{repo_name}.txt"

            process_files(str(repo_path), output_file, args.threshold, args.include_all) # Pass the absolute path as str
            logging.info(f"Successfully processed local repository at '{args.local_path}' into '{output_file}'.")


        else: # process from a public GitHub repository
            #Public repo is provided.
            from dpp import (download_repository,
                                                     process_files as epf,
                                                     is_text_file,
                                                     normalize_github_url)

            repo_name = Path(urlparse(args.repo_url).path).name  # extract repo name from URL
            output_file = args.output if args.output else f"{repo_name}.txt"  # Default name
            temp_dir = Path(f"temp_git2txt_{repo_name}")

            shutil.rmtree(temp_dir, ignore_errors=True)  # Clean dir

            temp_dir.mkdir(exist_ok = True)  # Make dir


            try:
                download_repository(args.repo_url, str(temp_dir)) # Call the function
                epf(str(temp_dir), output_file, args.threshold, args.include_all)  # Process files
                logging.info("Process of public repo finished") # Log process

            finally:
                shutil.rmtree(temp_dir, ignore_errors=True)

    except Exception as e:
        logging.error(f"An error occurred: {e}")
        exit(1)

if __name__ == "__main__":
    main()