import sys
import os
import subprocess

hit_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'contrib', 'hit'))
try:
    sys.path.append(hit_dir)
    import hit
except:
    subprocess.run(['make', 'bindings'], cwd=hit_dir)
    import hit

from hit import TokenType, Token
from .pyhit import Node, load, write, parse, tokenize
