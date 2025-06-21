import argparse
import chromadb
import openai
import os

from colorama import Fore, Style
from dotenv import load_dotenv

def main():
    """Ask a question about something in the notes and an AI answers it.
    """

    # Load the env variables
    load_dotenv('.env')

    # Argument parsing
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--query',
        help='Query to the Notes.app .'
    )
    parser.add_argument(
        '--db_path',
        default='./chroma',
        help='Path to the chroma vector database.'
    )
    parser.add_argument(
        '--index_name',
        default='notes',
        help='The name of the db collection.'
    )
    parser.add_argument(
        '--n_results',
        type=int,
        default=3,
        help='Number of documents to return'
    )
    parser.add_argument(
        '--debug',
        action='store_true'
    )
    args = parser.parse_args()

    # We initialize the ai client
    ai_client = openai.OpenAI(
        api_key=os.environ.get('API_KEY'),
        base_url=os.environ.get('BASE_URL')
    )

    # We initialize the chroma client and get the index
    chroma_client = chromadb.PersistentClient(
        path=args.db_path
    )
    index = chroma_client.get_collection(
        name=args.index_name
    )
    results = index.query(
        query_texts=[args.query],
        n_results=args.n_results
    )

    # We create a string representing the rag outputs.
    rag_result = ''
    for i in range(args.n_results):
        metadata = results['metadatas'][0][i] # type: ignore
        content = results['documents'][0][i] # type: ignore
        
        rag_result += f'------- document number {i} ------'
        rag_result += f'Metadata: {metadata}\n'
        rag_result += f'Content :\n         {content}\n\n\n'

    # We inject the rag output and the user question in the prompt
    with open('./prompts/rag_prompt.txt', 'r') as prompt_template:
        prompt = prompt_template.read().format(
            user_query=args.query,
            documents=rag_result
        )

    # We stream the answer from the ai client
    stream = ai_client.chat.completions.create(
        model='deepseek-chat',
        messages=[
            {'role': 'system', 'content': 'You are a helpul ai assistant.'},
            {'role': 'user', 'content': prompt}
        ],
        stream=True
    )

    if args.debug:
        print(f'\n{Fore.YELLOW}Prompt: {Fore.CYAN}{prompt}')
    
    print(f'{Fore.YELLOW}Response: \n{Fore.CYAN}')
    for chunk in stream:
        content = getattr(chunk.choices[0].delta, 'content', None)
        if content:
            print(content, end='', flush=True)
            
    print(f'{Style.RESET_ALL}')

if __name__ == "__main__":
    main()