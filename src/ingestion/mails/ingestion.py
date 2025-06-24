import imaplib
import logging
import os
import chromadb

from bs4 import BeautifulSoup
from email import policy
from email.parser import BytesParser
from typing import Dict, List
import chromadb.errors
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction


_logger = logging.getLogger(name='MAIL_INGESTION')


def get_mails(n_emails: int = 10) -> List[Dict[str, str]]:
    """Fetch the emails from the mail app.

    Args:
        n_emails (int): Number of mails to be fectched. starting at the last one.

    Returns:
        List[Dict[str, str]]: List of mail data.
    """

    # Connect to iCloud
    _logger.info('Extracting raw emails.')

    mail = imaplib.IMAP4_SSL("imap.mail.me.com")
    mail.login(os.environ.get('APPLE_EMAIL', ''), os.environ.get('APPLE_MAIL_KEY', ''))
    mail.select("inbox")

    # Fetch messages
    status, messages = mail.search(None, "ALL")
    if status != "OK" or not messages[0]:
        logging.error("Error: No messages found or search failed")
        mail.logout()
        exit()

    email_ids = messages[0].split()

    mails = []

    # Print emails from the last
    for num in email_ids[-n_emails:]:
        try:
            # Convert email ID to string if it's bytes
            email_id = num.decode() if isinstance(num, bytes) else str(num)
            
            # Fetch email data with BODY[] to get full message
            status, data = mail.fetch(email_id, "(BODY[])")
            
            # Check if data is in the expected format
            if not data or not isinstance(data, list) or len(data) == 0:
                _logger.warning(f"Error: No data returned for email {email_id}")
                continue
        
            # Extract raw email content
            raw_email = None
            for item in data:
                if isinstance(item, tuple) and len(item) > 1 and isinstance(item[1], bytes):
                    raw_email = item[1]  # Email content in bytes
                    break
            
            if raw_email is None:
                _logger.warning(f"Error: No valid email content found for {email_id}")
                continue
            
            mails.append(parse_raw_mail_data(raw_email, email_id))

            
        except Exception as e:
            print(f"Error processing email {num}: {str(e)}")

    mail.logout()
    return mails


def parse_raw_mail_data(raw_email: bytes, email_id: str) -> Dict[str, str]:
    """Parse a raw email into the correct format.

    Args:
        raw_email (bytes): raw bytes text email.
        email_id (str): mail id.

    Returns:
        Dict[str, str]: Parsed email.
    """
    
    # Parse email
    msg = BytesParser(policy=policy.default).parsebytes(raw_email)
    
    # Handling plain text or HTML body
    content = ''
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                soup = BeautifulSoup(part.get_content(), "html.parser")
                content += soup.get_text(separator=' ', strip=True)
                break  # Only print the first plain text part
    else:
        soup = BeautifulSoup(msg.get_content(), "html.parser")
        content = soup.get_text(separator=' ', strip=True)


    # Format the mail
    mail = {
        'from': msg['From'],
        'subject': msg['Subject'],
        'date': msg['Date'],
        'id':email_id,
        'content': content
    }

    return mail

def sync_mails_data(
        flush: bool,
        db_path: str,
        **kwargs: Dict
):
    """Synchronize the mails with the chroma database.

    Args:
        index_name (str): Collection name in the chroma db.
        flush (bool): If we re-create the collections.
        db_path (str): Location of the chroma db file.
    """

    # Fetch all the mails
    mails = get_mails()
    
    # Prepare the data
    _logger.info('Creating the docs, metadatas and ids...')

    documents = [mail['content'] for mail in mails]
    metadatas = [
        {
            'from': mail['from'],
            'subject': mail['subject'],
            'date': mail['date'],
        }
        for mail in mails
    ]
    ids = [mail['id'] for mail in mails]

    # Init the chroma client

    chroma_client = chromadb.PersistentClient(path=db_path)

    if flush:
        try:
            chroma_client.delete_collection(name='mails')
        except chromadb.errors.NotFoundError:
            _logger.info(f'the index -- mails -- does not exist.')

    index = chroma_client.get_or_create_collection(
        name='mails',
        embedding_function=SentenceTransformerEmbeddingFunction(
            model_name=os.environ.get('HF_EMBEDDING_MODEL', 'all-MiniLM-L6-v2')
        ) # type: ignore
    )

    # Update the index
    try:
        index.add(
            ids=ids,
            documents=documents,
            metadatas=metadatas # type: ignore
        )
    except Exception as e:
        _logger.error(e)
        _logger.error('Due to the error no element has been added to the database.')
    
    _logger.info('Chroma mails vector database is up to date.')