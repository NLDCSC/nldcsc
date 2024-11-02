import ast
import sys
from pathlib import Path


class GenEnv:

    def __init__(self, config_path: str = "config.py", overwrite: bool = False):
        self.config_path = Path(config_path)
        self.env_path  = self.config_path.parent / ".env"

        if overwrite or not self.env_path.exists():
            self.write_dotenv()
            print(f"Prepopulated .env file: {self.env_path.absolute()}")
            # Stop execution so .env can be filled.
            sys.exit(0)

    def write_dotenv(self):
        with open(self.env_path, "w") as fh:
            for config_value, next_line in self.get_config_values():
                line = f"{config_value}=\n" if next_line else f"\n{config_value}=\n"
                fh.write(line)

    def get_config_values(self):
        with open(self.config_path, "r") as fh:
            nodes = ast.parse(fh.read(), self.config_path, "exec")

        for node in nodes.body:
            # Optionally: `and node.name == "Config"`
            if isinstance(node, ast.ClassDef):
                previous_line_end = None
                for obj in node.body:
                    if isinstance(obj, ast.Assign):
                        targets = obj.targets
                        if len(targets) > 1:
                            raise Exception("Multiple assignments not supported")
                        target = targets[0]
                        # return ending line of the statement, not the target to deal with multiline statements
                        next_line = previous_line_end is None or target.lineno == previous_line_end + 1
                        previous_line_end = obj.end_lineno
                        yield target.id, next_line



