# Monthly_Reporting_(Phi_4).ipynb

This Jupyter Notebook generates a monthly report summarizing the development work done by a specified author within a given date range. The report includes summaries of commit messages and translations of these summaries into Ukrainian.

## File Path
`Monthly_Reporting_(Phi_4).ipynb`

## Key Components

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

7. **Output**:
   - Print the repository names, summaries, and translated summaries.
