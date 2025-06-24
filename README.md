
<p align="center">
  <img src="assets/logo.png" alt="Logo" width="400"/>
</p>




apple-rag-system is a Python project that native syncs data sources (macOS apps) to a ChromaDB vector database, creates embeddings using the all-MiniLM-L6-v2 model, and enables querying the data using Retrieval-Augmented Generation (RAG) with a language model.
The current version allows you to ask a LLM about your notes and your emails.
Features

### Upcoming

The following features are coming soon:
- Auto sync optimization.
- UI interface.
- LLM chat and not just QA.

Syncs data sources from the macOS apps to a ChromaDB vector database.
Generates embeddings using the all-MiniLM-L6-v2 model by default.
Allows users to ask questions about their notes and emails using RAG.
Simple command-line interface for syncing and querying.

## Prerequisites

- Python 3.12.9 or higher
- macOS (to access the apps)
- A valid API key compatible with the openai api.
- A valid Apple [password app](https://support.apple.com/en-ca/102654) 

## Setup
1. Clone the Repository: 
```
git clone https://github.com/BelG13/apple-rag-system.git
cd apple-rag-system
```

2. Create a Virtual Environment: 
```
python -m venv venv
source venv/bin/activate
```

3. Install Dependencies: 
```
pip install -r requirements.txt
```

4. Configure Environment Variables:

Create a .env file in the project root and add the following variables:
```
API_KEY=_api_key_here
BASE_URL='your base url here'
TOKENIZERS_PARALLELISM=true
HF_EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
DB_PATH='path to your chroma db, default is ./chroma'
APPLE_EMAIL_KEY='your apple password app'
APPLE_EMAIL='your apple email'
```

## Usage
### Sync data to ChromaDB
#### Manual Sync
To sync data from the macOS apps to the ChromaDB vector database and generate embeddings:
```
python main.py --mode='sync' --flush
```
Remove the flush argument if you want to update your vector database.

This command:

- Extracts data from the macOS apps data (notes and mails).
- Creates embeddings using the all-MiniLM-L6-v2 model.
- Stores the embeddings in ChromaDB.

#### Auto sync
To sync n automatically:
```
python main.py --mode='sync' --auto'
```

This command periodically and Extracts the data.

### Query 
To ask a question about your data using RAG:
```
python main.py --mode='query' --query="Your question here"
```

This command retrieves relevant data from ChromaDB and uses the language model to generate an answer.

## Notes

The HF_EMBEDDING_MODEL can be changed to another Hugging Face embedding model, but all-MiniLM-L6-v2 is the default.
Set TOKENIZERS_PARALLELISM to true or false based on your performance needs.

## Contributing
Contributions are welcome! Please open an issue or submit a pull request with improvements or bug fixes.
License
This project is licensed under the MIT License. See the LICENSE file for details.
