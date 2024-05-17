import argparse
import logging
import os
from collections import namedtuple
from subprocess import run, PIPE, STDOUT, CompletedProcess

from nldcsc.loggers.app_logger import AppLogger

logging.setLoggerClass(AppLogger)


class FlaskSqlMigrate(object):
    def __init__(self, cwd: str = None, app_ref: str = None):
        """
        app_ref:    The Flask application or factory function to load, in
                    the form 'module:name'. Module can be a dotted import
                    or file path. Name is not required if it is 'app',
                    'application', 'create_app', or 'make_app', and can be
                    'name(args)' to pass arguments.
        """
        self.logger = logging.getLogger(__name__)

        self.current_dir = (
            cwd if cwd is not None else os.path.dirname(os.path.realpath(__file__))
        )

        self._commands = namedtuple("commands", "INIT MIGRATE UPDATE STAMP")(1, 2, 3, 4)

        self.app_ref = app_ref

        if self.app_ref is not None:
            if "/" in self.app_ref:
                if os.path.exists(self.app_ref):
                    if ":" in self.app_ref:
                        self.current_dir = os.path.dirname(self.app_ref.split(":")[0])
                    else:
                        self.current_dir = os.path.dirname(self.app_ref)
                        if self.current_dir == "":
                            raise ValueError(
                                f"Could not parse parent dir from the given filename, please check and try again"
                            )
                else:
                    raise FileNotFoundError(
                        f"Cannot find the file you are referring to: {self.app_ref}, please check and try again!"
                    )
            else:
                if cwd is None:
                    raise AttributeError(
                        f"If you are providing a dotted module string, you need to provide a value for the "
                        f"'cwd' variable"
                    )
                else:
                    if not os.path.exists(self.current_dir):
                        raise FileNotFoundError(
                            f"Cannot find the directory you are referring to: {self.current_dir}, "
                            f"please check and try again!"
                        )

    @property
    def commands(self) -> namedtuple:
        return self._commands

    def db_init(self) -> None:
        res = self.__cli_runner(self.commands.INIT)
        self.__parse_command_output(res)

    def db_migrate(self) -> None:
        res = self.__cli_runner(self.commands.MIGRATE)
        self.__parse_command_output(res)

    def db_update(self) -> None:
        res = self.__cli_runner(self.commands.UPDATE)
        self.__parse_command_output(res)

    def db_stamp(self) -> None:
        res = self.__cli_runner(self.commands.STAMP)
        self.__parse_command_output(res)

    def __parse_command_output(self, cmd_output: CompletedProcess) -> None:
        if cmd_output.returncode != 0:
            self.logger.error(cmd_output.stdout)
        else:
            output_list = cmd_output.stdout.split("\n")

            for m in output_list:
                if m != "":
                    self.logger.info(m)

    def __cli_runner(self, command: int) -> CompletedProcess:
        command_mapping = {
            1: f"flask{f' --app {self.app_ref}' if self.app_ref is not None else ''} db init",
            2: f"flask{f' --app {self.app_ref}' if self.app_ref is not None else ''} db migrate",
            3: f"flask{f' --app {self.app_ref}' if self.app_ref is not None else ''} db upgrade",
            4: f"flask{f' --app {self.app_ref}' if self.app_ref is not None else ''} db stamp head",
        }
        try:
            result = run(
                command_mapping[command],  # nosec
                stdout=PIPE,
                stderr=STDOUT,
                universal_newlines=True,
                shell=True,
                cwd=self.current_dir,
            )
            return result
        except KeyError:  # pragma: no cover
            self.logger.error(f"Unknown command number received....")

    def __repr__(self) -> str:
        return f"<< FlaskSqlMigrate >>"


if __name__ == "__main__":
    argparser = argparse.ArgumentParser(
        description="migrate/update the database schema"
    )

    argparser.add_argument(
        "-i", action="store_true", help="Setup new migration directory"
    )
    argparser.add_argument("-m", action="store_true", help="Migrate the database")
    argparser.add_argument("-u", action="store_true", help="Update the database")
    argparser.add_argument(
        "-s",
        action="store_true",
        help="Stamp the head of the database to current state",
    )
    argparser.add_argument(
        "-a",
        "--app",
        type=str,
        help="The Flask application or factory function "
        "to load, in the form 'module:name'. Module can be a "
        "dotted import or file path. Name is not required if "
        "it is 'app', 'application', 'create_app', or 'make_app', "
        "and can be 'name(args)' to pass arguments.",
    )
    args = argparser.parse_args()

    if args.app:
        fsm = FlaskSqlMigrate(app_ref=args.app)
    else:
        fsm = FlaskSqlMigrate()

    if args.i:
        fsm.db_init()

    if args.m:
        fsm.db_migrate()

    if args.u:
        fsm.db_update()

    if args.s:
        fsm.db_stamp()
