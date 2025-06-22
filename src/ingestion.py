import subprocess
import chromadb
import logging
import re
import os

from typing import List, Dict, Optional
import chromadb.errors
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction


_logger = logging.getLogger('INGESTION')


def get_all_notes(ignore_empty_title: bool = True) -> List[Dict[str, str]]:
    """Run the osascript that get all the notes from the note app.

    Args:
        ignore_empty_title (bool, optional): Ignore the notes that don't have a title. Defaults to True.

    Returns:
        List[Dict[str, str]]: a list of dict, each dict represents a note and its data.
    """

    _logger.info('Running the osascript to extract the notes from the app')

    # We run the fetching script
    result = subprocess.run(['osascript', './applescripts/fetch_notes.scpt'], capture_output=True, text=True)
    return parse_raw_notes_data(result.stdout.strip(), ignore_empty_title)


def get_notes(initial_date: str = '2023-01-01-00-00-00', ignore_empty_title: bool = True) -> List[Dict[str, str]]:
    """Get all the notes starting at a given initial date.

    Args:
        initial_date (str, optional): the date the fetching start from. Defaults to '2023-01-01-00-00-00'.
        ignore_empty_title (bool, optional): Ignore the notes that don't have a title. Defaults to True.

    Returns:
        List[Dict[str, str]]: a list of dict, each dict represents a note and its data.
    """

    # Get all the notes and filter it
    notes = get_all_notes(ignore_empty_title)
    notes = [
        note for note in notes
        if note.get('created', '') > initial_date
    ]
    return notes

def parse_raw_notes_data(data: str, ignore_empty_title: bool = True) -> List[Dict[str, str]]:
    """Use the raw text output from the applescript and parse it into a dict.

    Args:
        data (str): the raw data coming from the output of the apple script.
        ignore_empty_title (bool, optional): Ignore the notes that don't have a title. Defaults to True.

    Returns:
        List[Dict[str, str]]: a list of dict, each dict represents a note and its data
    """

    notes = []
    ids = []

    # We iterate over the blocks and extract data from it
    for block in data.split("|||END|||"):
        if block.strip() == "":
            continue
        fields = block.split("|||SEP|||")
    
        if ignore_empty_title and not fields[0].strip():
            continue
        
        # We create a unique id
        note_id = str(hash((fields[0].strip(), fields[2].strip())))
        if note_id in ids:
            continue
        
        # We create a dict for the note, we remove the html-like tag in the content.
        # date format : '%Y-%m-%d-%H-%M-%S'
        note = {
            "title": fields[0].strip(),
            "content": fields[0].strip() + '\n' + re.sub('<.*?>', '', fields[1].strip()),
            "created": fields[2].strip(),
            "modified": fields[3].strip(),
            "folder": fields[4].strip()
        }
        notes.append(note)
        ids.append(note_id)

    return notes

def sync_notes_data(
        index_name: str,
        flush: bool,
        db_path: str,
        notes_data: Optional[List[Dict[str, str]]] | None = None,
        **kwargs: Dict,
):
    """Fetch the notes data and create a database out of it.

    Args:
        index_name (str): the index/collection name in the chroma database.
        flush (bool): If we want to delete the current index and completely rebuild the database.
        db_path (str): The path in wich the db will be stored.
        notes_data (Optional[List[Dict[str, str]]] | None) : If you want to update the db with some data.
    """

    # Fetch all the notes
    if not notes_data:
        notes = get_all_notes()
    else:
        notes = notes_data

    # Parse them for chromadb
    _logger.info('Creating the docs, metadatas and ids...')

    documents = [
        note.get('content', '')
        for note in notes
    ]

    metadatas = [
        {
            'title': note.get('title'),
            'created': note.get('created'),
            'folder': note.get('folder'),
        }
        for note in notes
    ]

    ids = [
        str(hash((note.get('title'), note.get('created'))))
        for note in notes
    ]


    # Init the chroma client
    _logger.info('ChromaDB vector database creation or update...')

    chroma_client = chromadb.PersistentClient(path=db_path)
    
    if flush:
        try:
            chroma_client.delete_collection(index_name)
        except chromadb.errors.NotFoundError:
            _logger.info(f'The index --{index_name}-- do not exist, we continue forward')

    chroma_client.get_or_create_collection(
        name=index_name,
        embedding_function=SentenceTransformerEmbeddingFunction(
            model_name=os.environ.get('HF_EMBEDDING_MODEL', 'all-MiniLM-L6-v2')
        ) # type: ignore
    )

    # Update the index
    index = chroma_client.get_collection(
        name=index_name
    )

    try:
        index.add(
            documents=documents,
            metadatas=metadatas, # type: ignore
            ids=ids
        )
    except Exception as e:
        _logger.error(e)
        _logger.warning('Due to the error no element has been added to the vector database.')

    _logger.info('Chromadb vector database up to date.')