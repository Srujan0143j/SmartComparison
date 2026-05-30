import sys
import os

# Put root directory into the python path so it can resolve the 'backend' imports correctly
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.main import app
