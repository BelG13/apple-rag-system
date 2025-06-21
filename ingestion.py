import subprocess
import chromadb
import logging
import re
import argparse
import os

from colorama import Fore, Style
from typing import List, Dict
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction


logging.basicConfig(
    level=logging.INFO,
    format=f'[{Fore.YELLOW}%(asctime)s] {Fore.LIGHTRED_EX}[%(levelname)s] {Fore.GREEN}%(name)s: {Fore.BLUE}%(message)s{Style.RESET_ALL}',
    datefmt='%Y-%m-%d %H:%M:%S'
)
_logger = logging.getLogger('INGESTION')


def run_applescript(script: str) -> str:
    """Run the osascript given as a argument

    Args:
        script (str): osascript you want to run in a subprocess.

    Returns:
        str: the output of the osascript.
    """

    _logger.info('Running the osascript to extract the notes from the app')
    result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
    return result.stdout.strip()

def get_all_notes(ignore_empty_title: bool = True) -> List[Dict[str, str]]:
    """Run the osascript that get all the notes from the note app.

    Args:
        ignore_empty_title (bool, optional): Ignore the notes that don't have a title. Defaults to True.

    Returns:
        List[Dict[str, str]]: a list of dict, each dict represent a note and its data.
    """

    script = '''
    set output to ""
    tell application "Notes"
        repeat with theNote in notes
            set noteTitle to the name of theNote
            set noteBody to the body of theNote
            try
                set noteCreated to the creation date of theNote
            on error
                set noteCreated to ""
            end try
            try
                set noteModified to the modification date of theNote
            on error
                set noteModified to ""
            end try
            try
                set folderName to the name of the container of theNote
            on error
                set folderName to ""
            end try

            set output to output & noteTitle & "|||SEP|||" & noteBody & "|||SEP|||" & noteCreated & "|||SEP|||" & noteModified & "|||SEP|||" & folderName & "|||END|||"
        end repeat
    end tell
    return output
    '''

    # We run the fetching script
    raw = run_applescript(script)
    notes = []
    ids = []

    # We iterate over the blocks and extract data from it
    for block in raw.split("|||END|||"):
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

def sync_notes_data(index_name: str, flush: bool, db_path: str):
    """Fetch the notes data and create a database out of it.

    Args:
        index_name (str): the index/collection name in the chroma database.
        flush (bool): If we want to delete the current index and completely rebuild the database.
        db_path (str): The path in wich the db will be stored.
    """

    # Fetch all the notes
    notes = get_all_notes()

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
        chroma_client.delete_collection(index_name)

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

def main():
    """Run the sync script.
    """

    # Argument Parsing
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--flush',
        action='store_true',
        default=False,
        help='If this flag is present we reset the chroma vector database'
    )
    parser.add_argument(
        '--index_name',
        type=str,
        default='notes',
        help='Name of the chromadb vector database collection'
    )
    parser.add_argument(
        '--db_path',
        default='./chroma',
        help='Location of the chromadb vector database file'
    )
    args = parser.parse_args()

    # run the syncclear
    sync_notes_data(
        index_name=args.index_name,
        flush=args.flush,
        db_path=args.db_path
    )


if __name__ == "__main__":
    main()