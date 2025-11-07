#!/usr/bin/env python
"""Tests for __main__ module."""

from unittest.mock import MagicMock, patch

from hoymiles_smiles.__main__ import parse_args


def test_parse_args_minimal():
    """Test parsing minimal required arguments."""
    with patch('sys.argv', ['hoymiles_smiles', '--dtu-host', '192.168.1.100']):
        args = parse_args()
        assert args.dtu_host == '192.168.1.100'
        assert args.dtu_port == 502
        assert args.query_period == 60


def test_parse_args_with_database():
    """Test parsing with database configuration."""
    with patch('sys.argv', [
        'hoymiles_smiles',
        '--dtu-host', '192.168.1.100',
        '--db-host', 'localhost',
        '--db-name', 'testdb',
    ]):
        args = parse_args()
        assert args.dtu_host == '192.168.1.100'
        assert args.db_host == 'localhost'
        assert args.db_name == 'testdb'
