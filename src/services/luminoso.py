from luminoso_api import LuminosoClient
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Connect to the Luminoso API
LuminosoClient.save_token(os.getenv("LUMINOSO_API_KEY"))
client = LuminosoClient.connect()