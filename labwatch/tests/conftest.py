import os
import sys

LABWATCH_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if LABWATCH_DIR not in sys.path:
    sys.path.insert(0, LABWATCH_DIR)
