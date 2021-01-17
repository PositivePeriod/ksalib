"""
Contains the core of ksalib
Please note that this module is private.  All functions and objects
are available in the main ``ksalib`` namespace - use that instead.
"""

from ksalib.ksa import Auth, Post, Sugang, Exploit, get_gaonnuri_board_post, get_gaonnuri_board
from ksalib.ksa import get_gaonnuri_oneline, get_student_points
from ksalib.parserlib import HTMLTableParser
from ksalib.simplefunctions import download

__all__ = [
    'Auth', 'Post', 'Sugang', 'Exploit', 'get_gaonnuri_board_post', 'get_gaonnuri_board', 'get_gaonnuri_oneline',
    'get_student_points']
__version__ = '1.0.0'
