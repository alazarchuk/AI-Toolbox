# -*- coding: utf-8 -*-
"""
monthly_reporting_ollama_local.py

This script fetches GitHub commits for specified organizations and a given date range,
generates a one-sentence summary for each repository's commits, and then
translates that summary into Ukrainian using a remote Ollama instance.

-----------------------------------------------------------------------------
Prerequisites:
1. Python 3.x installed.
2. An Ollama instance running and accessible on your network.
3. GitHub Personal Access Token with 'repo' scope.

-----------------------------------------------------------------------------
Setup:
1. Install required Python packages:
   pip install -r requirements.txt

2. Set the following environment variables in a .env file:
   GITHUB_TOKEN='your_github_personal_access_token'
   GITHUB_ORGANIZATIONS='org1,org2'
   OLLAMA_HOST='http://your-remote-machine-ip:11434'
   OLLAMA_MODEL='phi4'

3. Configure the Ollama settings in the script below.
-----------------------------------------------------------------------------
"""

# Step 1: Import required libraries
import os
import requests
from datetime import datetime
from collections import defaultdict
from github import Github, Auth
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


# --- Configuration ---
# Set your Ollama API endpoint and model via environment variables
# Set OLLAMA_HOST and OLLAMA_MODEL in your environment
# Example:
# export OLLAMA_HOST="http://your-remote-machine-ip:11434"
# export OLLAMA_MODEL="phi4"

# Read Ollama configuration from environment variables
OLLAMA_HOST = os.getenv('OLLAMA_HOST')
OLLAMA_MODEL = os.getenv('OLLAMA_MODEL')

if not OLLAMA_HOST or not OLLAMA_MODEL:
    raise ValueError(
        "Ollama host and model must be provided via environment variables.\n"
        "Please set 'OLLAMA_HOST' and 'OLLAMA_MODEL'."
    )

# Step 2: Set up GitHub access and parameters from environment variables
access_token = os.getenv('GITHUB_TOKEN')
github_organizations_str = os.getenv('GITHUB_ORGANIZATIONS')

if not access_token or not github_organizations_str:
    raise ValueError(
        "GitHub token and organizations must be provided via environment variables.\n"
        "Please set 'GITHUB_TOKEN' and 'GITHUB_ORGANIZATIONS'."
    )

# --- Ollama API Function ---
def generate_with_ollama(messages):
    """
    Sends a request to the Ollama API to generate text based on the provided messages.

    Args:
        messages (list): A list of message dictionaries in the Ollama chat API format.

    Returns:
        str: The generated text content from the model, or an error message.
    """
    api_url = f"{OLLAMA_HOST}/api/chat"
    payload = {
        "model": OLLAMA_MODEL,
        "messages": messages,
        "stream": False,
        "options": {
            "temperature": 0.0,
            "num_ctx": 14336
        }
    }
    try:
        response = requests.post(api_url, json=payload, timeout=60)
        response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)
        response_data = response.json()
        return response_data['message']['content']
    except requests.exceptions.RequestException as e:
        return f"Error connecting to Ollama: {e}"
    except KeyError:
        return "Error: Unexpected response format from Ollama."
    except Exception as e:
        return f"An unexpected error occurred: {e}"

github_organizations = github_organizations_str.split(",")
auth = Auth.Token(access_token)
g = Github(auth=auth)

# --- Define Reporting Period and Author ---
date_start = datetime.fromisoformat("2025-07-01")
date_end = datetime.fromisoformat("2025-08-01")
author_filter = g.get_user().login

print(f"Fetching commits for user '{author_filter}' between {date_start.date()} and {date_end.date()}")
print("-" * 60)

# Step 3: Fetch commits from GitHub
commits_per_repo = defaultdict(list)

for org_name in github_organizations:
    org_name = org_name.strip() # Clean up any whitespace
    try:
        org = g.get_organization(org_name)
        print(f"Scanning organization: {org_name}")
        for repo in org.get_repos():
            try:
                commits = repo.get_commits(since=date_start, until=date_end, author=author_filter)
                if commits.totalCount > 0:
                    repo_key = f"{org.name} -> {repo.name}"
                    print(f"  Found {commits.totalCount} commits in {repo_key}")
                    for commit in commits:
                        commits_per_repo[repo_key].append(commit.commit.message)
            except Exception as e:
                print(f"Could not process repo {repo.name}. Reason: {e}")
    except Exception as e:
        print(f"Could not access organization {org_name}. Reason: {e}")


# Step 4: Process commits for each repository to generate and translate summary
if not commits_per_repo:
    print("\nNo commits found for the specified user and period. Exiting.")
else:
    for repo, commits in commits_per_repo.items():
        # --- Generate Summary ---
        summary_prompt_messages = [
            {
                "role": "user",
                "content": f"""Write one sentence summary in the past tense about the work done, based on these commit messages.
                Keep it under 20 words.
                Exclude any mentions of pull requests, commits, and merges.
                Commits:
                {"\n".join(commits)}"""
            }
        ]

        print("=" * 60)
        print(repo)
        print("-" * 60)

        print("Generating summary...")
        summary = generate_with_ollama(summary_prompt_messages)
        print(f"Summary: {summary}")
        print("-" * 60)

        # --- Translate Summary ---
        translate_prompt_messages = [
            {"role": "system", "content": "You are a helpful assistant that translates development work summaries from English to Ukrainian."},
            {"role": "user", "content": "Fixed issues related to seeds and restoring files"},
            {"role": "assistant", "content": "Виправив помилки, пов'язані із сідами та відновленням файлів"},
            {"role": "user", "content": "Added additional fields to Address"},
            {"role": "assistant", "content": "Додав додаткові поля до Адреси"},
            {"role": "user", "content": "Refactored exception handling, enhanced code documentation and updated dependencies"},
            {"role": "assistant", "content": "Відрефакторив обробку помилок, покращив документацію коду і оновив залежності"},
            {"role": "user", "content": summary}
        ]

        print("Translating summary to Ukrainian...")
        translated_summary = generate_with_ollama(translate_prompt_messages)
        print(f"Переклад: {translated_summary}")
        print("=" * 60)
