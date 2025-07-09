import logging
import os
import re
import subprocess
from pathlib import Path

import requests
from git import Repo
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


@mcp.tool()
def get_all_repo_contents(repo_name: str, file_extensions=None):
    """
    Recursively reads all files in the given repo directory and returns their combined contents as a string.

    Args:
        repo_path (str): Path to the cloned repository.
        file_extensions (set): Set of file extensions to include (e.g., {'.py', '.md', '.txt'})

    Returns:
        str: Combined contents of all files as a single string.
    """

    # utility function to check and update repo in ./tmp directory
    check_if_repo_exists(repo_name)

    result = ""
    directory = "./tmp/" + repo_name

    all_contents = []
    ignore_list = {".git"}

    for root, dirs, files in os.walk(directory):
        dirs[:] = [d for d in dirs if d not in ignore_list]
        files = [f for f in files if f not in ignore_list]

        for file in files:
            if file_extensions is None or os.path.splitext(file)[1] in file_extensions:
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                        all_contents.append(
                            f"\n# File: {os.path.relpath(file_path, directory)}\n{content}"
                        )
                except Exception as e:
                    print(f"Skipping {file_path}: {e}")

    return "\n".join(all_contents)


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


@mcp.tool()
def get_recent_commits_with_diffs(repo_name: str, num_commits: int = 5):
    """
    Retrieves recent commit messages along with their diffs from a local Git repository.

    Args:
        repo_name (str): Name of the git repo.
        num_commits (int, optional): Number of recent commits to retrieve. Defaults to 5.

    Returns (str): A string containing commit messages and diffs, or None if the repository is invalid.
    """

    # utility function to check and update repo in ./tmp directory
    check_if_repo_exists(repo_name)

    directory = "./tmp/" + repo_name

    try:
        repo = Repo(directory)
        commits = list(repo.iter_commits("HEAD", max_count=num_commits))

        commit_details = []
        for commit in commits:
            message = f"Commit: {commit.hexsha}\nAuthor: {commit.author.name} <{commit.author.email}>\nDate: {commit.committed_datetime}\n\nMessage: {commit.message.strip()}\n"
            diffs = commit.diff(
                commit.parents[0] if commit.parents else None, create_patch=True
            )
            diff_text = "\n".join(
                d.diff.decode("utf-8", errors="ignore") for d in diffs
            )
            commit_details.append(f"{message}\nDiff:\n{diff_text}\n{'-'*80}")

        return "\n\n".join(commit_details)

    except Exception as e:
        print(f"Error: {e}")
        return "Could not fetch commits"


@mcp.tool()
def get_recent_issues_and_prs(owner: str, repo: str, num_items: int = 5):
    """
    Retrieves recent Issues and Pull Requests separately from a public GitHub repository using the REST API.

    Args:
        owner (str): Repository owner username (e.g., 'psf').
        repo (str): Repository name (e.g., 'requests').
        num_items (int, optional): Number of recent Issues and PRs to retrieve separately. Defaults to 5.

    Returns (str): A formatted string containing both Issues and PRs, or None on failure.
    """
    try:
        details = []

        # Fetch Issues (non-PRs only)
        issues_url = f"https://api.github.com/repos/{owner}/{repo}/issues"
        issues_params = {
            "state": "all",
            "per_page": 30,
            "sort": "created",
            "direction": "desc",
        }  # get more in case some are PRs
        issues_response = requests.get(issues_url, params=issues_params)
        issues_response.raise_for_status()

        issues_data = issues_response.json()
        real_issues = [item for item in issues_data if "pull_request" not in item][
            :num_items
        ]

        details.append(f"{'='*10} Recent Issues {'='*10}")
        if real_issues:
            for issue in real_issues:
                title = issue.get("title", "No title")
                number = issue.get("number", "N/A")
                author = issue.get("user", {}).get("login", "Unknown")
                state = issue.get("state", "Unknown")
                created_at = issue.get("created_at", "Unknown")
                body = (issue.get("body") or "").strip().replace("\n", " ")[:300]
                url = issue.get("html_url", "")

                details.append(
                    f"Issue #{number}: {title}\n"
                    f"Author: {author} | State: {state} | Created: {created_at}\n"
                    f"URL: {url}\n"
                    f"Body: {body}\n{'-'*80}"
                )
        else:
            details.append("No recent Issues found.\n" + "-" * 80)

        # Fetch Pull Requests
        prs_url = f"https://api.github.com/repos/{owner}/{repo}/pulls"
        prs_params = {
            "state": "all",
            "per_page": num_items,
            "sort": "created",
            "direction": "desc",
        }
        prs_response = requests.get(prs_url, params=prs_params)
        prs_response.raise_for_status()

        prs_data = prs_response.json()

        details.append(f"{'='*10} Recent Pull Requests {'='*10}")
        if prs_data:
            for pr in prs_data:
                title = pr.get("title", "No title")
                number = pr.get("number", "N/A")
                author = pr.get("user", {}).get("login", "Unknown")
                state = pr.get("state", "Unknown")
                created_at = pr.get("created_at", "Unknown")
                body = (pr.get("body") or "").strip().replace("\n", " ")[:300]
                url = pr.get("html_url", "")

                details.append(
                    f"PR #{number}: {title}\n"
                    f"Author: {author} | State: {state} | Created: {created_at}\n"
                    f"URL: {url}\n"
                    f"Body: {body}\n{'-'*80}"
                )
        else:
            details.append("No recent Pull Requests found.\n" + "-" * 80)

        return "\n\n".join(details)

    except Exception as e:
        print(f"Error: {e}")
        return f"Error: {e}"


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
