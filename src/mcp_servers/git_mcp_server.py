import logging
import os
import re
import subprocess
from pathlib import Path
from typing import List

from mcp.server.fastmcp import FastMCP

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)-8s %(message)s",
    datefmt="%m/%d/%y %H:%M:%S",
)

mcp = FastMCP(name="Git")


def check_if_repo_exists(repo_name: str):
    """Check if the specified repo exists in the /tmp folder, else persist it.

    Args:
        repo_name (str): name of the repo with organization, e.g. org/repo

    Returns: None
    """

    destination_path = "./tmp/"
    folder_path = Path(destination_path + repo_name)

    if folder_path.is_dir():
        logging.info(f"The repo '{repo_name}' already exists, skipping clone...")
    else:
        logging.info(f"Repo '{repo_name}' does not exist, cloning...")

        repo_url = "https://github.com/" + repo_name
        subprocess.run(["git", "clone", repo_url, folder_path], check=True)

        logging.info(f"Successfully cloned repo: {repo_name}.")


# FIXME: To handle files with same name and files with absolute or relative paths.
def search_and_read_file(folder_path: str, filename: str):
    """Search for a file in the folder_path and return it's contents if it exists.

    If the `filename` contains parent directory along with the filename, only pass the filename as the parameter.

    Args:
        folder_path (str): Folder path to search the file in.
        filename (str): Only the file name without it's parent directory. E.g. `README.md` or `main.py`.

    Returns: Returns the contents of the file if found.
    """
    for root, _, files in os.walk(folder_path):
        if filename in files:
            file_path = os.path.join(root, filename)
            with open(file_path, "r") as file:
                return file.read()
    return f"File: {filename}, not found in the repo..."


@mcp.tool()
def file_content_parser(repo_name: str, filename: str):
    """Retrieve and fetch contents of the specifiled file.

    Args:
        repo_name (str): Name of the repository to search the file in.
        filename (str): Name of the file to be fetched.

    Returns: File contents of the specified file if found.
    """

    # utility function to check and update repo in ./tmp directory
    check_if_repo_exists(repo_name)

    return search_and_read_file(folder_path="./tmp/" + repo_name, filename=filename)


@mcp.tool()
def get_repo_structure(repo_name: str):
    """Get the directory structure of the specified repository.

    Args:
        repo_name (str): Name of the repository.

    Returns: Directory structure of the repo.
    """

    # utility function to check and update repo in ./tmp directory
    check_if_repo_exists(repo_name)

    result = ""
    directory = "./tmp/" + repo_name

    ignore_list = {".git"}

    for root, dirs, files in os.walk(directory):
        dirs[:] = [d for d in dirs if d not in ignore_list]
        files = [f for f in files if f not in ignore_list]

        level = root.replace(directory, "").count(os.sep)
        indent = " " * 4 * level
        result += f"{indent}{os.path.basename(root)}/\n"
        sub_indent = " " * 4 * (level + 1)
        for file in files:
            result += f"{sub_indent}{file}\n"

    return result


@mcp.tool()
def code_search(repo_name: str, search_pattern: str) -> str:
    """Find all occurances of a particular string pattern within the repo.

    You can customize the pattern_to_search variable to match specific code patterns or functions. For example:
    - To find function definitions: r"^\s*def\s+\w+\s*\("
    - To find specific function calls: r"my_function\("

    Args:
        repo_name (str): Name of the repository.
        search_pattern (str): Pattern to search for in the repository.

    Returns: List of all occurences of the specified search pattern from the repository as a string.
    """

    # utility function to check and update repo in ./tmp directory
    check_if_repo_exists(repo_name)

    results = []
    directory = "./tmp/" + repo_name

    regex = re.compile(search_pattern)
    # regex = re.compile(r"^\s*def\s+\w+\s*\(")

    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".py"):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        for line_no, line in enumerate(f, start=1):
                            if regex.search(line):
                                results.append(
                                    {
                                        "file_path": file_path,
                                        "line_no": line_no,
                                        "content": line.strip(),
                                    }
                                )
                except Exception as e:
                    logging.error(f"Error reading {file_path}: {e}")

    return str(results)


if __name__ == "__main__":
    # Transport methods: ['stdio', 'sse', 'streamable-http']
    transport = "stdio"

    if transport == "stdio":
        logging.info("Running with stdio transport")
        mcp.run(transport="stdio")
    elif transport == "sse":
        logging.info("Running with sse transport")
        mcp.run(transport="sse")
    elif transport == "streamable-http":
        logging.info("Running with streamable-http transport")
        mcp.run(transport="streamable-http")
    else:
        raise ValueError(f"Invalid transport format: {transport}")
