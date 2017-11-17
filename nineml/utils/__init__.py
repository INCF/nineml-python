"""
This module contains general purpose utility functions used throughout the
library.
"""
from __future__ import absolute_import

from .path import join_norm, restore_sys_path, is_file_handle
from .equality import nearly_equal, xml_equal
from .validation import (
    check_inferred_against_declared, validate_identifier,
    assert_no_duplicates)
