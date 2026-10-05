# -*- coding: utf-8 -*-
"""
monthly_reporting_ollama.py

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

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta
import os
import sys

from dotenv import load_dotenv
from github import Auth, Github, GithubException
import requests


# --- Configuration ---
@dataclass
class Config:
    """Configuration settings loaded from environment variables."""

    ollama_host: str
    ollama_model: str
    github_token: str
    github_organizations: list[str]
    timeout: int = 600

    @classmethod
    def from_env(cls) -> "Config":
        """
        Loads configuration from environment variables.

        Raises:
            ValueError: If required environment variables are missing.
        """
        load_dotenv()

        ollama_host = os.getenv("OLLAMA_HOST")
        ollama_model = os.getenv("OLLAMA_MODEL")
        if not ollama_host or not ollama_model:
            raise ValueError(
                "Ollama host and model must be provided via environment variables.\n"
                "Please set 'OLLAMA_HOST' and 'OLLAMA_MODEL'."
            )

        github_token = os.getenv("GITHUB_TOKEN")
        github_organizations_str = os.getenv("GITHUB_ORGANIZATIONS")
        if not github_token or not github_organizations_str:
            raise ValueError(
                "GitHub token and organizations must be provided via environment variables.\n"
                "Please set 'GITHUB_TOKEN' and 'GITHUB_ORGANIZATIONS'."
            )

        github_organizations = [
            org.strip()
            for org in github_organizations_str.split(",")
            if org.strip()
        ]

        return cls(
            ollama_host=ollama_host.rstrip("/"),
            ollama_model=ollama_model,
            github_token=github_token,
            github_organizations=github_organizations,
        )


def get_previous_month_date_range(
    reference_date: datetime | None = None,
) -> tuple[datetime, datetime]:
    """
    Computes the start and end dates for the previous month.

    Args:
        reference_date: Reference date (defaults to current date/time).

    Returns:
        tuple[datetime, datetime]: (date_start, date_end) representing the first day
        of the previous month and the first day of the reference month.
    """
    today = reference_date or datetime.now()
    # First day of current month
    date_end = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    # First day of previous month
    date_start = (date_end - timedelta(days=1)).replace(day=1)
    return date_start, date_end


# --- Ollama API Client ---
class OllamaClient:
    """Client for interacting with the Ollama chat API."""

    def __init__(self, host: str, model: str, timeout: int = 600):
        self.host = host.rstrip("/")
        self.model = model
        self.timeout = timeout

    def generate(self, messages: list[dict[str, str]], temperature: float = 0.0) -> str:
        """
        Sends a request to the Ollama API to generate text based on the provided messages.

        Args:
            messages (list): A list of message dictionaries in the Ollama chat API format.
            temperature (float): Sampling temperature for generation. Defaults to 0.0.

        Returns:
            str: The generated text content from the model, or an error message.
        """
        api_url = f"{self.host}/api/chat"
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature,
            },
        }
        try:
            response = requests.post(api_url, json=payload, timeout=self.timeout)
            response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)
            response_data = response.json()
            return response_data["message"]["content"]
        except requests.exceptions.RequestException as e:
            return f"Error connecting to Ollama: {e}"
        except (KeyError, TypeError):
            return "Error: Unexpected response format from Ollama."
        except Exception as e:  # pylint: disable=broad-exception-caught
            return f"An unexpected error occurred: {e}"

    def summarize_commits(self, commits: list[str]) -> str:
        """
        Generates a concise one-sentence summary for a list of commit messages.

        Args:
            commits: List of commit message strings.

        Returns:
            str: Generated summary text.
        """
        commits_text = "\n".join(commits)
        prompt_content = (
            "Write one sentence summary in the past tense about the work done, "
            "based on these commit messages.\n"
            "Keep it under 20 words.\n"
            "Exclude any mentions of pull requests, commits, and merges. Use passive voice.\n"
            "Commits:\n"
            f"{commits_text}"
        )
        summary_prompt_messages = [
            {
                "role": "user",
                "content": prompt_content,
            }
        ]
        return self.generate(summary_prompt_messages)

    def translate_to_ukrainian(self, text: str) -> str:
        """
        Translates a development summary from English to Ukrainian.

        Args:
            text: English summary string.

        Returns:
            str: Ukrainian translation.
        """
        translate_prompt_messages = [
            {
                "role": "system",
                "content": (
                    "You are a helpful assistant that translates development "
                    "work summaries from English to Ukrainian."
                ),
            },
            {
                "role": "user",
                "content": "Fixed issues related to seeds and restoring files",
            },
            {
                "role": "assistant",
                "content": "Виправив помилки, пов'язані із сідами та відновленням файлів",
            },
            {"role": "user", "content": "Added additional fields to Address"},
            {"role": "assistant", "content": "Додав додаткові поля до Адреси"},
            {
                "role": "user",
                "content": (
                    "Refactored exception handling, enhanced code documentation "
                    "and updated dependencies"
                ),
            },
            {
                "role": "assistant",
                "content": (
                    "Відрефакторив обробку помилок, покращив документацію коду і "
                    "оновив залежності"
                ),
            },
            {"role": "user", "content": text},
        ]
        return self.generate(translate_prompt_messages)

    def summarize_overall(self, summaries: list[str]) -> str:
        """
        Synthesizes multiple repository summaries into a cohesive 3-4 sentence overall summary.

        Args:
            summaries: List of repository summary strings.

        Returns:
            str: 3-4 sentence summary in English.
        """
        summaries_text = "\n".join(f"- {s}" for s in summaries)
        prompt_content = (
            "Write a consolidated development summary based on the following "
            "repository summaries.\n"
            "Summarize the work done into exactly 3 to 4 sentences in the past tense.\n"
            "Use passive voice.\n"
            "Exclude any mentions of pull requests, commits, and merges.\n"
            "Place each sentence on its own line.\n"
            "Output only the 3-4 sentences without bullet points, numbering, or "
            "introductory text.\n\n"
            "Repository summaries:\n"
            f"{summaries_text}"
        )
        messages = [{"role": "user", "content": prompt_content}]
        return self.generate(messages).strip()

    def translate_overall_to_ukrainian(self, text: str) -> str:
        """
        Translates a multi-sentence development summary from English to Ukrainian
        using impersonal/passive voice (e.g., 'Реалізовано...', 'Перенесено...').

        Args:
            text: English summary string.

        Returns:
            str: Ukrainian translation.
        """
        messages = [
            {
                "role": "system",
                "content": (
                    "You are a helpful assistant that translates development work summaries "
                    "from English to Ukrainian. Maintain an impersonal past-tense style "
                    "(e.g., 'Реалізовано...', 'Перенесено...', 'Оновлено...'). "
                    "Translate each sentence accurately on its own line and output only "
                    "the translated text without any introductory comments."
                ),
            },
            {
                "role": "user",
                "content": (
                    "New SEO features were implemented, image quota statistics and optimization "
                    "progress were updated, and a modernization roadmap was added.\n"
                    "Shopify session storage was migrated, billing, plan management, and API "
                    "pagination were updated, and Gumbo was replaced with Nokogiri for "
                    "HTML parsing.\n"
                    "Security vulnerabilities were patched, dependencies were upgraded, table "
                    "markup guidelines were restricted, and various bugs were resolved."
                ),
            },
            {
                "role": "assistant",
                "content": (
                    "Реалізовано нові SEO-функції, оновлено статистику квот на зображення і "
                    "прогрес оптимізації, а також додано дорожню карту модернізації.\n"
                    "Перенесено сховище сесій Shopify, оновлено білінг, управління планами "
                    "та пагінацію API, а також замінено Gumbo на Nokogiri для парсингу HTML.\n"
                    "Усунено вразливості безпеки, оновлено залежності, обмежено правила "
                    "розмітки таблиць та виправлено різні помилки."
                ),
            },
            {"role": "user", "content": text},
        ]
        return self.generate(messages).strip()


# Backward compatibility helper
def generate_with_ollama(
    messages: list[dict[str, str]],
    host: str | None = None,
    model: str | None = None,
) -> str:
    """
    Sends a request to the Ollama API to generate text based on the provided messages.
    Maintained for backward compatibility.

    Args:
        messages (list): A list of message dictionaries in the Ollama chat API format.
        host (str, optional): Ollama host URL. Defaults to OLLAMA_HOST env var.
        model (str, optional): Ollama model name. Defaults to OLLAMA_MODEL env var.

    Returns:
        str: The generated text content from the model, or an error message.
    """
    load_dotenv()
    resolved_host = host or os.getenv("OLLAMA_HOST")
    resolved_model = model or os.getenv("OLLAMA_MODEL")
    if not resolved_host or not resolved_model:
        return (
            "Error: Ollama host and model must be provided via arguments or "
            "environment variables ('OLLAMA_HOST' and 'OLLAMA_MODEL')."
        )
    client = OllamaClient(host=resolved_host, model=resolved_model)
    return client.generate(messages)


# --- GitHub Service ---
class GitHubService:
    """Service for interacting with GitHub repositories and fetching commit data."""

    def __init__(self, token: str):
        auth = Auth.Token(token)
        self.client = Github(auth=auth)

    def get_authenticated_user_login(self) -> str:
        """Retrieves the username of the authenticated token owner."""
        return self.client.get_user().login

    def _fetch_repo_commits(
        self,
        repo,
        start_date: datetime,
        end_date: datetime,
        author: str | None = None,
    ) -> list[str]:
        """Fetches commit messages for a single repository."""
        kwargs = {"since": start_date, "until": end_date}
        if author:
            kwargs["author"] = author

        commits = repo.get_commits(**kwargs)
        if commits.totalCount == 0:
            return []

        return [commit.commit.message for commit in commits]

    def fetch_commits_by_repo(
        self,
        organizations: list[str],
        start_date: datetime,
        end_date: datetime,
        author: str | None = None,
    ) -> dict[str, list[str]]:
        """
        Fetches commit messages grouped by repository for specified organizations.

        Args:
            organizations: List of organization names to scan.
            start_date: Start of the date range filter.
            end_date: End of the date range filter.
            author: GitHub username filter (optional).

        Returns:
            dict[str, list[str]]: Mapping from repository display name to commit messages.
        """
        commits_per_repo: dict[str, list[str]] = defaultdict(list)

        for org_name in organizations:
            org_name = org_name.strip()
            if not org_name:
                continue

            try:
                org = self.client.get_organization(org_name)
                print(f"Scanning organization: {org_name}")
                for repo in org.get_repos():
                    try:
                        repo_commits = self._fetch_repo_commits(
                            repo=repo,
                            start_date=start_date,
                            end_date=end_date,
                            author=author,
                        )
                        if repo_commits:
                            repo_key = f"{org.name} -> {repo.name}"
                            print(f"  Found {len(repo_commits)} commits in {repo_key}")
                            commits_per_repo[repo_key].extend(repo_commits)
                    except (GithubException, requests.exceptions.RequestException) as repo_err:
                        print(f"Could not process repo {repo.name}. Reason: {repo_err}")
                    except Exception as repo_err:  # pylint: disable=broad-exception-caught
                        print(f"Could not process repo {repo.name}. Reason: {repo_err}")
            except (GithubException, requests.exceptions.RequestException) as org_err:
                print(f"Could not access organization {org_name}. Reason: {org_err}")
            except Exception as org_err:  # pylint: disable=broad-exception-caught
                print(f"Could not access organization {org_name}. Reason: {org_err}")

        return dict(commits_per_repo)


# --- Report Generator ---
@dataclass
class RepoReport:
    """Report data container for a single repository."""

    repo_name: str
    commits: list[str]
    summary: str
    translated_summary: str


@dataclass
class FinalReport:
    """Consolidated final report container."""

    english_summary: str
    ukrainian_summary: str

    def format_output(self) -> str:
        """Formats the final report matching the requested ENG and UKR format."""
        return f"ENG:\n{self.english_summary}\nUKR:\n{self.ukrainian_summary}"


class MonthlyReportGenerator:
    """Coordinates fetching commits, generating summaries, and translating them."""

    def __init__(
        self,
        config: Config,
        github_service: GitHubService | None = None,
        ollama_client: OllamaClient | None = None,
    ):
        self.config = config
        self.github_service = github_service or GitHubService(config.github_token)
        self.ollama_client = ollama_client or OllamaClient(
            host=config.ollama_host,
            model=config.ollama_model,
            timeout=config.timeout,
        )

    def generate_reports(self, reference_date: datetime | None = None) -> list[RepoReport]:
        """
        Gathers commits and generates summarized and translated reports for each repo.

        Args:
            reference_date: Optional reference date to compute the report period.

        Returns:
            list[RepoReport]: List of generated reports per repository.
        """
        date_start, date_end = get_previous_month_date_range(reference_date)
        author_filter = self.github_service.get_authenticated_user_login()

        print(
            f"Fetching commits for user '{author_filter}' "
            f"between {date_start.date()} and {date_end.date()}"
        )
        print("-" * 60)

        commits_per_repo = self.github_service.fetch_commits_by_repo(
            organizations=self.config.github_organizations,
            start_date=date_start,
            end_date=date_end,
            author=author_filter,
        )

        if not commits_per_repo:
            print("\nNo commits found for the specified user and period.")
            return []

        reports: list[RepoReport] = []
        for repo, commits in commits_per_repo.items():
            summary = self.ollama_client.summarize_commits(commits)
            translated_summary = self.ollama_client.translate_to_ukrainian(summary)
            reports.append(
                RepoReport(
                    repo_name=repo,
                    commits=commits,
                    summary=summary,
                    translated_summary=translated_summary,
                )
            )

        return reports

    @staticmethod
    def print_reports(reports: list[RepoReport]) -> None:
        """Prints formatted reports to standard output."""
        if not reports:
            print("No reports to display.")
            return

        for report in reports:
            print("=" * 60)
            print(report.repo_name)
            print("-" * 60)
            print(f"Summary: {report.summary}")
            print("-" * 60)
            print(f"Переклад: {report.translated_summary}")
            print("=" * 60)

    def assemble_final_report(
        self,
        reports: list[RepoReport] | None = None,
        reference_date: datetime | None = None,
    ) -> FinalReport | None:
        """
        Assembles the final report summarized into 3-4 sentences using AI.

        Synthesizes individual repository summaries into a cohesive 3-4 sentence
        overview and translates it to Ukrainian in an impersonal voice.

        Args:
            reports: Optional list of RepoReport instances. If not provided, generates them.
            reference_date: Optional reference date to compute the report period.

        Returns:
            FinalReport | None: The assembled final report, or None if no reports available.
        """
        if reports is None:
            reports = self.generate_reports(reference_date)

        if not reports:
            return None

        summaries = [f"{report.repo_name}: {report.summary}" for report in reports]
        english_summary = self.ollama_client.summarize_overall(summaries)
        ukrainian_summary = self.ollama_client.translate_overall_to_ukrainian(english_summary)

        return FinalReport(
            english_summary=english_summary,
            ukrainian_summary=ukrainian_summary,
        )

    @staticmethod
    def print_final_report(final_report: FinalReport | None) -> None:
        """
        Prints the final report in the requested ENG / UKR format to stdout.

        Args:
            final_report: FinalReport instance to display.
        """
        if not final_report:
            print("\nNo final report to display.")
            return

        print("\n" + "=" * 60)
        print(final_report.format_output())
        print("=" * 60)

    def assemble_and_output_final_report(
        self,
        reports: list[RepoReport] | None = None,
        reference_date: datetime | None = None,
    ) -> FinalReport | None:
        """
        Assembles and outputs the final report to stdout.

        Args:
            reports: Optional list of RepoReport instances. If not provided, generates them.
            reference_date: Optional reference date to compute the report period.

        Returns:
            FinalReport | None: The assembled final report.
        """
        final_report = self.assemble_final_report(reports, reference_date)
        self.print_final_report(final_report)
        return final_report

    def run(
        self, reference_date: datetime | None = None
    ) -> tuple[list[RepoReport], FinalReport | None]:
        """
        Executes the monthly reporting workflow, prints per-repository reports,
        and assembles and outputs the final consolidated report.

        Args:
            reference_date: Optional reference date to compute the report period.

        Returns:
            tuple[list[RepoReport], FinalReport | None]: Generated reports and final report.
        """
        reports = self.generate_reports(reference_date)
        if not reports:
            return [], None

        self.print_reports(reports)
        final_report = self.assemble_final_report(reports)
        self.print_final_report(final_report)
        return reports, final_report


def main() -> None:
    """Main application entry point."""
    try:
        config = Config.from_env()
    except ValueError as err:
        print(f"Configuration error:\n{err}", file=sys.stderr)
        sys.exit(1)

    generator = MonthlyReportGenerator(config)
    generator.run()


if __name__ == "__main__":
    main()
