import os
import sys
import click
from importlib import util
import pkgutil

from nldcsc.plugins.sql_migrate import SqlMigrate


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
@click.option("--config", help="Path to the sqlmigrate config", required=False)
@click.pass_context
def db(ctx, version, debug, config=None):
    """Perform database migrations."""

    if version:
        SqlMigrate.get_version(True)
        exit(0)

    if not config:
        click.echo("Please provide a config file!")
        exit(1)

    if debug:
        SqlMigrate.set_logger_debug_format()

    try:
        package = os.path.dirname(os.path.abspath(config))

        while "__init__.py" in os.listdir(package):
            package = os.path.dirname(package)
            config = os.path.relpath(os.path.abspath(config), package)

        os.chdir(package)

        sys.path.insert(0, package)
        spec = util.spec_from_file_location("sql_migrate_migrate_config", config)
        c = util.module_from_spec(spec)
        spec.loader.exec_module(c)

        sys.path.pop(0)
    except (AttributeError, FileNotFoundError, ModuleNotFoundError) as e:
        click.echo(f"Config file not found -> {e}, try running from the project root.")
        exit(1)

    if not hasattr(c, "db") or not hasattr(c, "metadata"):
        click.echo("Invalid config file, db and/or metadata does not exist!")
        exit(1)

    sql_migrate = SqlMigrate(c.db, c.metadata)

    ctx.ensure_object(SqlMigrate)
    ctx.obj = sql_migrate


@db.command()
@click.pass_context
def list_templates(ctx):
    """List available templates."""
    ctx.obj.list_templates(True)


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
@click.pass_context
def init(ctx, directory, template, package):
    """Creates a new migration repository."""
    ctx.obj.init(directory=directory, template=template, package=package)


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
@click.pass_context
def revision(
    ctx,
    message,
    autogenerate,
    sql,
    head,
    splice,
    branch_label,
    version_path,
):
    """Create a new revision file."""
    ctx.obj.revision(
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
@click.pass_context
def migrate(ctx, message, sql, head, splice, branch_label, version_path):
    """Autogenerate a new revision file (Alias for 'revision --autogenerate')"""
    ctx.obj.migrate(
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
@click.pass_context
def upgrade(ctx, sql, tag, x_arg, revision, max_lookback_days, sync):
    """Upgrade to a later version"""
    ctx.obj.upgrade(
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
@click.pass_context
def check(ctx, revision, max_lookback_days, sync):
    """Upgrade to a later version"""
    if revision == -1:
        revision = None

    table_list = ctx.obj.check(
        revision=revision, max_lookback_days=max_lookback_days, sync=sync
    )

    if revision is None:
        click.echo("Missing migrations:")
    else:
        click.echo(f"Migration steps for {revision}:")

    if len(table_list) != 1:
        from tabulate import tabulate

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
@click.pass_context
def downgrade(ctx, sql, tag, x_arg, revision):
    """Downgrade to a earlier version"""
    ctx.obj.downgrade(revision=revision, sql=sql, tag=tag, x_arg=x_arg)


@db.command()
@click.pass_context
def drop(ctx):
    """Drop all tables in the database and clear migrations directory"""
    ctx.obj.drop()


@db.command()
@click.pass_context
def history(ctx):
    """Request the current migration history of the database"""
    table_list = ctx.obj.history()

    from tabulate import tabulate

    click.echo(tabulate(table_list, headers="firstrow", tablefmt="fancy_grid"))
