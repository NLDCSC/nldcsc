import click
from nldcsc.plugins.sql_migrate.cli import db

@click.group()
def cli():
    pass

cli.add_command(db)
