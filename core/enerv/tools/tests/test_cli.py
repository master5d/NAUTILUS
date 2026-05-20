import pytest
from click.testing import CliRunner
from tools.tools.cli import facet

def test_cli_help():
    runner = CliRunner()
    result = runner.invoke(facet, ['--help'])
    assert result.exit_code == 0
    assert 'Usage:' in result.output
    assert 'audit' in result.output
    assert 'index' in result.output
