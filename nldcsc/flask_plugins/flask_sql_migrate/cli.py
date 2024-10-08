import click
from flask import current_app
from flask.cli import with_appcontext
from tabulate import tabulate


@click.group(invoke_without_command=True)
@click.option(
    "-v",
    "--version",
    is_flag=True,
    help="Show the current version of SqlMigrate and Alembic and exit",
)
@click.option(
    "-d",
    "--debug",
    is_flag=True,
    help="Set logging output to DEBUG",
)
@with_appcontext
def db(version, debug):
    """Perform database migrations."""
    if version:
        current_app.extensions["migrate"].migrate.get_version(True)
        exit(0)
    if debug:
        current_app.extensions["migrate"].migrate.set_logger_debug_format()


@db.command()
@with_appcontext
def list_templates():
    """List available templates."""
    current_app.extensions["migrate"].migrate.list_templates(True)


@db.command()
@click.option(
    "-d",
    "--directory",
    default=None,
    help='Migration script directory (default is "migrations")',
)
@click.option(
    "-t",
    "--template",
    default=None,
    help='Repository template to use (default is "flask")',
)
@click.option(
    "--package",
    is_flag=True,
    help="Write empty __init__.py files to the environment and version locations",
)
@with_appcontext
def init(directory, template, package):
    """Creates a new migration repository."""
    current_app.extensions["migrate"].migrate.init(
        directory=directory, template=template, package=package
    )


@db.command()
@click.option("-m", "--message", default=None, help="Revision message")
@click.option(
    "--autogenerate",
    is_flag=True,
    help=(
        "Populate revision script with candidate migration operations, based on comparison of database to model"
    ),
)
@click.option(
    "--sql",
    is_flag=True,
    help="Don't emit SQL to database - dump to standard output instead",
)
@click.option(
    "--head",
    default="head",
    help="Specify head revision or <branchname>@head to base new revision on",
)
@click.option(
    "--splice",
    is_flag=True,
    help='Allow a non-head revision as the "head" to splice onto',
)
@click.option(
    "--branch-label",
    default=None,
    help="Specify a branch label to apply to the new revision",
)
@click.option(
    "--version-path",
    default=None,
    help="Specify specific path from config for version file",
)
@with_appcontext
def revision(
    message,
    autogenerate,
    sql,
    head,
    splice,
    branch_label,
    version_path,
):
    """Create a new revision file."""
    current_app.extensions["migrate"].migrate.revision(
        message=message,
        autogenerate=autogenerate,
        sql=sql,
        head=head,
        splice=splice,
        branch_label=branch_label,
        version_path=version_path,
    )


@db.command()
@click.option("-m", "--message", default=None, help="Revision message")
@click.option(
    "--sql",
    is_flag=True,
    help="Don't emit SQL to database - dump to standard output instead",
)
@click.option(
    "--head",
    default="head",
    help="Specify head revision or <branchname>@head to base new revision on",
)
@click.option(
    "--splice",
    is_flag=True,
    help='Allow a non-head revision as the "head" to splice onto',
)
@click.option(
    "--branch-label",
    default=None,
    help="Specify a branch label to apply to the new revision",
)
@click.option(
    "--version-path",
    default=None,
    help="Specify specific path from config for version file",
)
@with_appcontext
def migrate(message, sql, head, splice, branch_label, version_path):
    """Autogenerate a new revision file (Alias for 'revision --autogenerate')"""
    current_app.extensions["migrate"].migrate.migrate(
        message=message,
        sql=sql,
        head=head,
        splice=splice,
        branch_label=branch_label,
        version_path=version_path,
    )


@db.command()
@click.option(
    "--sql",
    is_flag=True,
    help="Don't emit SQL to database - dump to standard output instead",
)
@click.option(
    "--tag",
    default=None,
    help='Arbitrary "tag" name - can be used by custom env.py scripts',
)
@click.option(
    "-x",
    "--x-arg",
    multiple=True,
    help="Additional arguments consumed by custom env.py scripts",
)
@click.option(
    "--max-lookback-days",
    "-D",
    default=30,
    help="Amount of days revisions can be older than the current revision",
)
@click.option(
    "--sync",
    "-s",
    is_flag=True,
    help="Sync the old formatted migration files to the DB. Only available if no newly formatted migrations have been migrated.",
)
@click.argument("revision", default="head")
@with_appcontext
def upgrade(sql, tag, x_arg, revision, max_lookback_days, sync):
    """Upgrade to a later version"""
    current_app.extensions["migrate"].migrate.upgrade(
        revision=revision,
        sql=sql,
        tag=tag,
        x_arg=x_arg,
        max_lookback_days=max_lookback_days,
        sync=sync,
    )


@db.command()
@click.option(
    "--max-lookback-days",
    "-D",
    default=30,
    help="Amount of days revisions can be older than the current revision",
)
@click.option(
    "--sync",
    "-s",
    is_flag=True,
    help="Sync the old formatted migration files to the DB. Only available if no newly formatted migrations have been migrated.",
)
@click.argument("revision", default=-1)
@with_appcontext
def check(revision, max_lookback_days, sync):
    """Upgrade to a later version"""
    if revision == -1:
        revision = None

    table_list = current_app.extensions["migrate"].migrate.check(
        revision=revision, max_lookback_days=max_lookback_days, sync=sync
    )

    if revision is None:
        click.echo("Missing migrations:")
    else:
        click.echo(f"Migration steps for {revision}:")

    if len(table_list) != 1:
        click.echo(tabulate(table_list, headers="firstrow", tablefmt="fancy_grid"))
    else:
        click.echo("None")


@db.command()
@click.option(
    "--sql",
    is_flag=True,
    help="Don't emit SQL to database - dump to standard output instead",
)
@click.option(
    "--tag",
    default=None,
    help='Arbitrary "tag" name - can be used by custom env.py scripts',
)
@click.option(
    "-x",
    "--x-arg",
    multiple=True,
    help="Additional arguments consumed by custom env.py scripts",
)
@click.argument("revision", default="-1")
@with_appcontext
def downgrade(sql, tag, x_arg, revision):
    """Downgrade to a earlier version"""
    current_app.extensions["migrate"].migrate.downgrade(
        revision=revision, sql=sql, tag=tag, x_arg=x_arg
    )


@db.command()
@with_appcontext
def drop():
    """Drop all tables in the database and clear migrations directory"""
    current_app.extensions["migrate"].migrate.drop()


@db.command()
@with_appcontext
def history():
    """Request the current migration history of the database"""
    table_list = current_app.extensions["migrate"].migrate.history()
    click.echo(tabulate(table_list, headers="firstrow", tablefmt="fancy_grid"))
