import ast
import sys
from pathlib import Path

from nldcsc.generic.utils import getenv_list


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
            if isinstance(node, ast.ClassDef):
                previous_line_end = None
                for obj in node.body:
                    if isinstance(obj, ast.Assign):
                        try:
                            env_key, default_value = self.process_node(obj=obj)
                            if env_key is None:
                                continue
                            next_line = (
                                previous_line_end is None
                                or obj.lineno == previous_line_end + 1
                            )
                            previous_line_end = obj.end_lineno
                            yield env_key, default_value, next_line
                        except Exception as e:
                            print(
                                f"Failed to process assignment on line {obj.lineno}:", e
                            )

    def process_node(self, obj: ast.Assign):
        # Optionally: `and node.name == "Config"`
        if isinstance(obj.value, ast.Call):
            # os.environ.get or os.getenv
            function_node = obj.value.func
            function_name = (
                function_node.attr
                if hasattr(function_node, "attr")
                else function_node.id
            )
            if function_name not in [
                "getenv",
                "get",
                "getenv_bool",
                "getenv_list",
                "getenv_dict",
            ]:
                print(
                    f"Skipping line {obj.lineno} with unknown function {function_name}."
                )
                return None, None
            env_key = obj.value.args[0].value
            # Note that the default value of dotenv for an empty .env (`A=`) is '' and not None.
            if not self.keep_defaults or len(obj.value.args) == 1:
                # Skip default value processing.
                default_value = None
            else:
                # Process default value, can be of different types.
                default_value_node = obj.value.args[1]
                if not isinstance(default_value_node, ast.Constant):
                    print(
                        f"Can't insert default for {env_key} on {obj.lineno} - leaving blank."
                    )
                    default_value = ""
                else:
                    default_value = default_value_node.value
        elif isinstance(obj.value, ast.Subscript) and obj.value.value.attr == "environ":
            # environ[]
            env_key = obj.value.slice.value
            default_value = False
        else:
            print(f"Failed to parse line {obj.lineno} - skipping.")
            return None, None

        return env_key, default_value
