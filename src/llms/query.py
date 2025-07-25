import chromadb

from typing import Dict, Literal
from colorama import Fore, Style
from .memory import Agent

from src.utils import get_logger
_logger = get_logger(name='QUERY')

def query(
        query: str,
        db_path: str,
        n_results: int,
        debug: bool,
        api_key: str,
        base_url: str,
        **kwargs: Dict

):
    """_summary_

    Args:
        index_name (str): Name of the collection 
        query (str): Question for the LLM.
        db_path (str): path to the database.
        n_results (int): Number of document to get with rag.
        debug (bool): True for debug mode.
        api_key (str): oai compatible api key.
        base_url (str): oai compatible base url.
    """

    # We initialize the ai client
    _logger.info('Initialize the Agent')
    agent = Agent(
        api_key=api_key,
        base_url=base_url,
        model='deepseek-chat'
    )

    # We initialize the chroma client and get the index
    _logger.info('Connect to the vector database...')
    chroma_client = chromadb.PersistentClient(
        path=db_path
    )

    # Conversation loop
    _logger.info(f'Starting the conversation loop : \n')
    while query:

        # We get the rag content
        rag_content = '========= Notes =========\n'
        rag_content += get_rag_content(chroma_client, 'notes', query, n_results)

        rag_content += '========= Mails =========\n'
        rag_content += get_rag_content(chroma_client, 'mails', query, n_results)

        # We inject the rag output and the user question in the prompt
        with open('./prompts/rag_prompt.txt', 'r') as prompt_template:
            prompt = prompt_template.read().format(
                user_query=query,
                documents=rag_content
            )

        # We stream the answer from the ai client
        agent.query(
            prompt=prompt,
            stream=True
        )

        print(f'{Fore.BLUE}Your turn ? : {Fore.LIGHTRED_EX}', sep='', flush=True)
        query = input()

def get_rag_content(
        client,
        index_name: Literal['notes', 'mails'],
        query: str,
        n_results: int) -> str:

    index = client.get_collection(
        name=index_name
    )
    
    results = index.query(
        query_texts=[query],
        n_results=n_results
    )
    
    try:
        rag_result = ''
        for i in range(n_results):
            metadata = results['metadatas'][0][i] # type: ignore
            content = results['documents'][0][i] # type: ignore
            
            rag_result += f'------- document number {i} ------'
            rag_result += f'Metadata: {metadata}\n'
            rag_result += f'Content :\n         {content}\n\n\n'

    except IndexError as e:
        _logger.error(e)
        _logger.warning('Recollecting less documents.')

    finally:
        rag_result = ''
        for i in range(len(results['ids'][0])):
            metadata = results['metadatas'][0][i] # type: ignore
            content = results['documents'][0][i] # type: ignore
            
            rag_result += f'------- document number {i} ------'
            rag_result += f'Metadata: {metadata}\n'
            rag_result += f'Content :\n         {content}\n\n\n'

    return rag_result