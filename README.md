# g2t-py(git to text - python): Convert Git Repositories to Text Files (Python)

This command-line tool downloads a GitHub repository (public or local) and concatenates its contents into a single text file. It's useful for code analysis, documentation, or feeding codebase data into LLMs for various AI tasks.

It has been inspired from and converted to python heavily relying on the [original git2txt repo](https://github.com/addyosmani/git2txt) by [Addy Osmani](https://github.com/addyosmani).

## Features

- Downloads public GitHub repositories or processes local Git repositories.
- Combines repository content into a single text file.
- Automatically excludes binary files (configurable).
- Configurable file size threshold (configurable).

## Installation

```bash
pip install argparse mimetypes
```

(These are standard library and basic types libraries that should be included and/or standard on your python installation)

Usage

```bash
python git2txt.py [options] <repository_url>
```

or

```bash
python git2txt.py [options] -l <local_repository_path>
```

You must provide either a GitHub repository URL or a local repository path, but not both.

### Arguments

- <repository_url>: The URL of the public GitHub repository to download and convert. This is required unless you use the -l option.

- Supported URL Formats:

  - HTTPS URLs: https://github.com/username/repository
  - Short format: username/repository (assumes https://github.com/)
  - SSH URLs: git@github.com:username/repository

#### Options

- -l <local_repository_path> or --local-path <local_repository_path>: Specifies the path to a local Git repository that has already been cloned. If this option is used, the tool will process the files in the local repository directly, without attempting to download anything.

- -o <output_file> or --output <output_file>: Specifies the output file path. If not specified, defaults to <repository_name>.txt in the current directory.

- -t <threshold_mb> or --threshold <threshold_mb>: Sets the file size threshold in megabytes (MB). Files larger than this threshold will be skipped. Default is 0.1 MB (100 KB).

- --include-all: Includes all files, regardless of size or type. Binary files will be processed, and the size threshold will be ignored. Use with caution! This is useful for non-code assets.

- --debug: Enables debug mode with verbose logging. This will print detailed information about which files are being processed and skipped, along with any errors that occur.

### Examples:

Convert a public GitHub repository:

```bash
python git2txt.py https://github.com/pallets/flask -o flask.txt
```

This will download the Flask repository from GitHub and create a file named flask.txt in the current directory containing the combined content of all text files in the repository (excluding files larger than 100KB).

Convert a public GitHub repository with a custom threshold:

```bash
python git2txt.py https://github.com/pallets/flask -o flask.txt -t 2
```

This will download the Flask repository, but only include files smaller than 2MB.

Convert all files in a GitHub repository including images and large files:

```bash
python git2txt.py https://github.com/pallets/flask --include-all -o all_files.txt
```

Downloads all content.

Process a locally cloned repository:

```bash
python git2txt.py -l /path/to/my/local/repo -o local_repo.txt
```

This will process the files in the local repository located at /path/to/my/local/repo and create a file named local_repo.txt. The tool expects this directory to contain a .git subdirectory, indicating that it is a valid Git repository. The tool will not attempt to download anything.

Run with debug output:

```bash
python git2txt.py https://github.com/pallets/flask --debug
```

This will enable debug mode, providing more detailed logging output to the console.

Output Format
The tool generates a text file with the following format:

```
================================================================================
File: path/to/file.txt
Size: 1.2 KB
================================================================================

[File contents here]

================================================================================
File: another/file.js
Size: 4.5 KB
================================================================================

[File contents here]
```

Each file's content is preceded by a separator line, the file path (relative to the repository root), and the file size. This structured output makes it easier to parse the resulting text file programmatically.

### Error Handling

The tool provides informative error messages for common issues such as:

Invalid GitHub repository URL

Failure to download the repository

Failure to read or decode a file

Invalid local path

### License

This README provides clear instructions on how to use the Python `g2tpy` tool, including all the options and arguments, supported URL formats, and expected output format. It should be easy for users to understand and get started with the tool.
