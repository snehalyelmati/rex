import os
import subprocess
from pathlib import Path

from mcp.server.fastmcp import FastMCP

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
        print(f"The repo '{folder_path}' already exists, skipping clone...")
    else:
        print(f"Repo '{folder_path}' does not exist, cloning...")

        repo_url = "https://github.com/" + repo_name
        subprocess.run(["git", "clone", repo_url, folder_path], check=True)

        print(f"Successfully cloned repo: {repo_name}.")


def search_and_read_file(folder_path: str, filename: str):
    """Search for a file in the folder_path and return it's contents if it exists.

    Args:
        folder_path (str): Folder path to search the file in.
        filename (str): File to search for.

    Returns: Returns the contents of the file if found.
    """
    for root, _, files in os.walk(folder_path):
        if filename in files:
            file_path = os.path.join(root, filename)
            with open(file_path, "r") as file:
                return file.read()
    return None


@mcp.tool()
def file_content_parser(repo_name: str, filename: str):
    """Retrieve and read file contents for the specified file.

    Args:
        repo_name (str): Name of the repository to search the file in.
        filename (str): Name of the file to be read.

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
    for root, _, files in os.walk(directory):
        level = root.replace(directory, "").count(os.sep)
        indent = " " * 4 * level
        result += f"{indent}{os.path.basename(root)}/\n"
        sub_indent = " " * 4 * (level + 1)
        for file in files:
            result += f"{sub_indent}{file}\n"

    return result


if __name__ == "__main__":
    # Transport methods: ['stdio', 'sse', 'streamable-http']
    transport = "stdio"

    if transport == "stdio":
        print("Running with stdio transport")
        mcp.run(transport="stdio")
    elif transport == "sse":
        print("Running with sse transport")
        mcp.run(transport="sse")
    elif transport == "streamable-http":
        print("Running with streamable-http transport")
        mcp.run(transport="streamable-http")
    else:
        raise ValueError(f"Invalid transport format: {transport}")
