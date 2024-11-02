import ast
import sys
from pathlib import Path


class GenEnv:

    def __init__(
        self,
        config_path: str = "config.py",
        overwrite: bool = False,
        keep_defaults: bool = True,
    ):

        self.config_path = Path(config_path)
        self.env_path = self.config_path.parent / ".env"
        self.keep_defaults = keep_defaults

        if overwrite or not self.env_path.exists():
            self.write_dotenv()
            print(f"Prepopulated .env file: {self.env_path.absolute()}")
            # Stop execution so .env can be filled.
            sys.exit(0)

    def write_dotenv(self):
        with open(self.env_path, "w") as fh:
            seen_keys = []
            # skip_next is used to pass line skipping to next keypair if required.
            skip_next = False
            for config_key, default_value, next_line in self.get_config_values():
                # default_value is False if no default, None if default is None and otherwise a value.
                if config_key in seen_keys:
                    print(
                        f"Already seen {config_key} - not duplicating in .env - manually check defaults."
                    )
                    continue
                if default_value is None:
                    # Never write None to .env. There is no way to specify them. `A=` will lead to A = "".
                    skip_next = True
                    continue
                elif self.keep_defaults or not default_value:
                    seen_keys.append(config_key)
                    default_value = "" if not default_value else default_value
                    line = (
                        f"{config_key}={default_value}\n"
                        if next_line and not skip_next
                        else f"\n{config_key}={default_value}\n"
                    )
                    fh.write(line)
                    skip_next = False

    def get_config_values(self):
        with open(self.config_path, "r") as fh:
            nodes = ast.parse(fh.read(), self.config_path, "exec")

        for node in nodes.body:
            # Optionally: `and node.name == "Config"`
            if isinstance(node, ast.ClassDef):
                previous_line_end = None
                for obj in node.body:
                    if isinstance(obj, ast.Assign):
                        if isinstance(obj.value, ast.Call):
                            # environ.get or getenv
                            function_name = obj.value.func.attr
                            if function_name not in ["getenv", "get"]:
                                print(
                                    f"Skipping line {obj.lineno} with unknown function {function_name}."
                                )
                                continue
                            env_key = obj.value.args[0].value
                            # Note that the default value of dotenv for an empty .env (`A=`) is '' and not None.
                            default_value = (
                                obj.value.args[1].value
                                if len(obj.value.args) == 2
                                else None
                            )
                        elif (
                            isinstance(obj.value, ast.Subscript)
                            and obj.value.value.attr == "environ"
                        ):
                            # environ[]
                            env_key = obj.value.slice.value
                            default_value = False
                        else:
                            print(f"Failed to parse line {obj.lineno} - skipping.")
                            continue

                        next_line = (
                            previous_line_end is None
                            or obj.lineno == previous_line_end + 1
                        )
                        previous_line_end = obj.end_lineno
                        yield env_key, default_value, next_line
