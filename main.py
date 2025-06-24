import argparse
import os
import logging

from src.ingestion.notes.ingestion import sync_notes_data
from src.ingestion.mails.ingestion import sync_mails_data
from src.ingestion.auto_sync.listen import start_auto_sync
from src.query import query

from dotenv import load_dotenv
from colorama import Fore, Style

logging.basicConfig(
    level=logging.INFO,
    format=f'[{Fore.YELLOW}%(asctime)s] {Fore.LIGHTRED_EX}[%(levelname)s] {Fore.GREEN}%(name)s: {Fore.BLUE}%(message)s{Style.RESET_ALL}',
    datefmt='%Y-%m-%d %H:%M:%S'
)


def main():
    """Handle the ingestion and the interaction with the LLM.
    """

    # Load the env variables
    load_dotenv('.env')

    # Init the argument parser
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--mode',
        choices=[
            'sync',
            'query'
        ]
    )

    # General arguments
    parser.add_argument(
        '--debug',
        action='store_true'
    )

    # Sync args
    parser.add_argument(
        '--flush',
        action='store_true',
        default=False,
        help='If this flag is present we reset the chroma vector database'
    )
    parser.add_argument(
        '--auto',
        action='store_true'
    )

    # Query args
    parser.add_argument(
        '--query',
        help='Query to the Notes.app .'
    )
    parser.add_argument(
        '--n_results',
        type=int,
        default=3,
        help='Number of documents to return'
    )

    # get the args values
    args = parser.parse_args()
    
    if args.mode == 'sync' and args.auto:
        start_auto_sync()
        
    elif args.mode == 'sync':
        sync_notes_data(db_path=os.environ.get('DB_PATH', './chroma'), **vars(args))
        sync_mails_data(db_path=os.environ.get('DB_PATH', './chroma'), **vars(args))

    elif args.mode == 'query':
        query(
            api_key=os.environ.get('API_KEY', ''),
            base_url=os.environ.get('BASE_URL', ''),
            db_path=os.environ.get('DB_PATH', './chroma'),
            **vars(args)
        )


if __name__ == '__main__':
    main()