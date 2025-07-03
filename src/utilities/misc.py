from pathlib import Path
import subprocess
import os


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
        subprocess.run(["git", "clone", repo_url, destination_path], check=True)

        print(f"Successfully cloned repo: {repo_name}.")


def search_and_read_file(folder_path: str, filename: str):
    """Search for a file in the folder_path and return it's contents if it exists.

    Args:
        folder_path (str): Folder path to search the file in.
        filename (str): File to search for.

    Returns: Returns the contents of the file if found.
    """
    for root, dirs, files in os.walk(folder_path):
        if filename in files:
            file_path = os.path.join(root, filename)
            with open(file_path, "r") as file:
                return file.read()
    return None
