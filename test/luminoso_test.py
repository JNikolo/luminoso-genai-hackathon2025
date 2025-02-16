import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.services.luminoso import client

def test_luminoso():
    project_info_list = client.get('/projects/')
    print(project_info_list[0]["project_id"])

test_luminoso()