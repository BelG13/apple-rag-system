import chromadb
import time
import logging
import argparse
import os

from src.ingestion import get_all_notes, sync_notes_data

from colorama import Fore, Style
from dotenv import load_dotenv


logging.basicConfig(
    level=logging.INFO,
    format=f'[{Fore.YELLOW}%(asctime)s] {Fore.LIGHTRED_EX}[%(levelname)s] {Fore.GREEN}%(name)s: {Fore.BLUE}%(message)s{Style.RESET_ALL}',
    datefmt='%Y-%m-%d %H:%M:%S'
)
_logger = logging.getLogger(name='AUTO-SYNC')


class Listerner():

    def __init__(self, index_name: str):
        """Initialize the listener object. connect to the db and get the number of records.

        Args:
            index_name (str): Name of the collection.
        """
        
        # Get db credentials
        self.connect_to_db(index_name)

        # Get current number of elements in the db
        self.last_number_fetched = len(self.metadatas) # type: ignore

    def connect_to_db(self, index_name:str):
        """Connect to the chromadb database and get the index and metadatas.

        Args:
            index_name (str): Name of the collection.
        """
        # Connect to the database
        self.chroma_client = chromadb.PersistentClient(path=os.environ.get('DB_PATH', './chroma'))
        self.index = self.chroma_client.get_collection(name=index_name)
        self.metadatas = self.index.get(include=['metadatas']).get('metadatas', [])

    def find_number_fectched(self):
        """Get the current number of notes in the Note.app

        Returns:
            int: Number of notes
        """
        notes_data = get_all_notes()
        return len(notes_data)

    def start(self):
        """Start and monitor the listening of the Note.app.
        Trigger a syncronization if the database is not up to date.
        """
        
        _logger.info('Starting auto-sync')
        try:
            while True:

                if self.last_number_fetched == self.find_number_fectched(): # type: ignore
                    _logger.info('The database is up to date.')
                    time.sleep(20)
                    continue
                
                _logger.info('The database is not up to date.')
                sync_notes_data(
                    index_name='notes',
                    flush=True,
                    db_path='./chroma',
                )

        except KeyboardInterrupt:
            _logger.info('The user stopped the server with crtl-c')



def main():
    """handle the auto-sync process
    """
    
    # Load the .env variables
    load_dotenv('.env')

    # handle the commandline args
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--index_name',
        default='notes'
    )
    args = parser.parse_args()

    # Monitoring
    listener = Listerner(**vars(args))
    listener.start()

if __name__ == '__main__':
    main()