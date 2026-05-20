import click
from .commands.audit import audit
from .commands.validate import validate
from .commands.new import new
from .commands.index import index
from .commands.init import init
from .commands.migrate import migrate
from .commands.migrate_folder import migrate_folder
from .commands.auto_index import auto_index_cli
from .commands.current_info import current_info_cli
from .commands.visualize import visualize
from .commands.ingest import ingest

@click.group()
def facet():
    """Faceted indexing system for project and knowledge folders."""
    pass

facet.add_command(audit)
facet.add_command(validate)
facet.add_command(new)
facet.add_command(index)
facet.add_command(init)
facet.add_command(migrate)
facet.add_command(migrate_folder)
facet.add_command(auto_index_cli)
facet.add_command(current_info_cli)
facet.add_command(visualize)
facet.add_command(ingest)

def main():
    facet()
