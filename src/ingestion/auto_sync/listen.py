import chromadb
import time
import logging
import os

from src.ingestion.notes.ingestion import get_all_notes, sync_notes_data
from src.ingestion.mails.ingestion import get_mails, sync_mails_data

from colorama import Fore, Style
from typing import Literal


logging.basicConfig(
    level=logging.INFO,
    format=f'[{Fore.YELLOW}%(asctime)s] {Fore.LIGHTRED_EX}[%(levelname)s] {Fore.GREEN}%(name)s: {Fore.BLUE}%(message)s{Style.RESET_ALL}',
    datefmt='%Y-%m-%d %H:%M:%S'
)
_logger = logging.getLogger(name='AUTO-SYNC')


class Listerner():

    def __init__(self):
        """Initialize the listener object. connect to the db and get the number of records.

        Args:
            index_name (str): Name of the collection.
        """
        
        # Get db credentials
        self.connect_to_db()

        # Get current number of elements in the notes
        self.last_number_fetched = len(self.ids['notes']) # type: ignore

        # Get the last id for the emails
        self.last_email_db_id = max(self.ids['mails'])


    def connect_to_db(self):
        """Connect to the chromadb database and get the index and ids.

        Args:
            index_name (str): Name of the collection.
        """
        # Connect to the database
        self.chroma_client = chromadb.PersistentClient(path=os.environ.get('DB_PATH', './chroma'))
        self.indexes = {
            index: self.chroma_client.get_collection(name=index)
            for index in ['notes', 'mails']
        }
        self.ids = {
            index: self.indexes[index].get(include=[])['ids']
            for index in ['notes', 'mails']
        }

    def is_fetchable(self, index_name: Literal['notes', 'mails']):
        """Get the current number of notes in the Note.app

        Returns:
            int: Number of notes
        """

        if index_name == 'notes':
            notes_data = get_all_notes()
            return not (self.last_number_fetched == len(notes_data)), len(notes_data)
        
        elif index_name == 'mails':
            last_email_app_id = get_mails(n_emails=1)[0]['id']
            return not (last_email_app_id == self.last_email_db_id), last_email_app_id

    def start(self):
        """Start and monitor the listening of the Note.app.
        Trigger a syncronization if the database is not up to date.
        """
        
        _logger.info('Starting auto-sync')
        try:
            while True:
                
                # Notes auto sync 
                note_sync_flag, total_notes_number = self.is_fetchable('notes')

                if not note_sync_flag:
                    _logger.info('Notes are up to date.')
                else:
                    _logger.info('Notes are not up to date.')
                    sync_notes_data(
                        flush=True,
                        db_path=os.environ.get('DB_PATH', './chroma'),
                    )
                    self.last_number_fetched = total_notes_number

                # Mails  auto sync
                mail_sync_flag, last_mail_id = self.is_fetchable('mails')

                if not mail_sync_flag:
                    _logger.info('Mails are up to date.')
                else:
                    _logger.info('Mails are not up to date.')
                    sync_mails_data(
                        flush=False,
                        db_path=os.environ.get('DB_PATH', './chroma')
                    )
                    self.last_email_db_id = last_mail_id
                
                time.sleep(10)


        except KeyboardInterrupt:
            _logger.info('The user stopped the server with crtl-c')



def start_auto_sync():
    """handle the auto-sync process
    """
    # Monitoring
    listener = Listerner()
    listener.start()