import argparse
import os

from dotenv import load_dotenv


import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.ingestion.notes.ingestion import sync_notes_data
from src.ingestion.mails.ingestion import sync_mails_data
from src.ingestion.auto_sync.listen import start_auto_sync
from src.llms.query import query


def main():
    """Handle the ingestion and the interaction with the LLM.
    """

    # Load the env variables
    load_dotenv('.env')

    # Init the argument parser
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--sync',
        action='store_true',
        help='The action is to syncronize.'
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
    
    if args.sync and args.auto:
        start_auto_sync()
        
    elif args.sync:
        sync_notes_data(db_path=os.environ.get('DB_PATH', './chroma'), **vars(args))
        sync_mails_data(db_path=os.environ.get('DB_PATH', './chroma'), **vars(args))

    elif args.query:
        query(
            api_key=os.environ.get('API_KEY', ''),
            base_url=os.environ.get('BASE_URL', ''),
            db_path=os.environ.get('DB_PATH', './chroma'),
            **vars(args)
        )


if __name__ == '__main__':
    main()