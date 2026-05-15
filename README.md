# AI Toolbox

This repository contains a collection of AI tools and utilities.

## Monthly_Reporting_(Phi_4).ipynb

This Jupyter Notebook generates a monthly report summarizing the development work done by a specified author within a given date range. The report includes summaries of commit messages and translations of these summaries into Ukrainian.

### File Path
`Monthly_Reporting_(Phi_4).ipynb`

### Key Components

1. **Install Dependencies**:
   - `transformers`
   - `accelerate`
   - `bitsandbytes`
   - `PyGithub`

2. **Import Libraries**:
   - `torch`
   - `transformers`
   - `datetime`
   - `google.colab.userdata`
   - `github`
   - `collections.defaultdict`

3. **Model Setup**:
   - Load the `microsoft/phi-4` model for text generation.
   - Configure the model for 4-bit quantization using `BitsAndBytesConfig`.

4. **GitHub Authentication**:
   - Authenticate using a GitHub token stored in Google Colab's userdata.

5. **Fetch Commits**:
   - Retrieve commits from specified GitHub organizations and repositories within the given date range and for the specified author.

6. **Summarize Commits**:
   - Use the text generation model to create summaries of commit messages.
   - Translate the summaries into Ukrainian.

### Output
- Print the repository names, summaries, and translated summaries.

## monthly_reporting_ollama.py

This script fetches GitHub commits for specified organizations and a given date range, generates a one-sentence summary for each repository's commits, and translates that summary into Ukrainian using a remote Ollama instance.

### Prerequisites

1.  **Python 3.x**: Ensure Python is installed on your system.
2.  **Ollama**: An Ollama instance must be running and accessible on your network.
3.  **GitHub Token**: A Personal Access Token with `repo` scope is required.

### Setup

1.  **Virtual Environment**: Create and activate a virtual environment:
    ```bash
    python -m venv .venv
    source .venv/bin/activate
    ```

2.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

3.  **Environment Variables**: Create a `.env` file in the root directory and add the following:
    ```env
    GITHUB_TOKEN='your_github_personal_access_token'
    GITHUB_ORGANIZATIONS='org1,org2'
    OLLAMA_HOST='http://your-remote-machine-ip:11434'
    OLLAMA_MODEL='phi4'
    ```

### Running the Script

Activate the virtual environment and execute the script:
```bash
source .venv/bin/activate
python monthly_reporting_ollama.py
```

