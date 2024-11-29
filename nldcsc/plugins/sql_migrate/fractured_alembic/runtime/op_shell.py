from alembic.operations import Operations, MigrateOperation, BatchOperations
from alembic.operations import ops


def get_shell_obj(
    name: str, attr: str, cb: callable, reverse_obj: object = None, batch: bool = False
):
    if batch and attr.startswith("batch_"):
        batch_alt = attr
        attr = attr.removeprefix("batch_")
    elif batch:
        batch_alt = f"batch_{attr}"

    class shell_base(MigrateOperation):
        @classmethod
        def _classmethod(cls, operations, *args, **kwargs):
            cb(cls, operations, *args, **kwargs)

    def __init__(self, *args, **kwargs):
        ...

    def reverse(*args, **kwargs):
        if reverse_obj is not None:
            return reverse_obj(*args, **kwargs)

    dyn_class = {
        "__init__": __init__,
        attr: shell_base._classmethod,
        "reverse": reverse,
    }

    if batch:
        dyn_class[batch_alt] = shell_base._classmethod

    shell = type(name, (shell_base,), dyn_class)

    if batch:
        return BatchOperations.register_operation(attr, batch_alt)(shell)
    return Operations.register_operation(attr)(shell)


def create_shell(skip: set = None, cb: callable = lambda: ...):
    shell_objects = {}

    if skip is None:
        skip = set()

    for cls in [Operations, BatchOperations]:
        for attr in dir(cls):
            if attr in skip:
                # skip list
                continue

            op_name = "".join(p.capitalize() for p in attr.split("_")) + "Op"
            batch = False

            if cls == BatchOperations:
                batch = True

            if op_name.startswith("Batch"):
                continue

            if not hasattr(ops, op_name):
                continue

            shell_objects[attr] = get_shell_obj(f"{attr}_class", attr, cb, batch=batch)

    shell_objects["execute"] = get_shell_obj(
        "execute_class", "execute", cb, batch=False
    )
    shell_objects["execute"] = get_shell_obj("execute_class", "execute", cb, batch=True)

    return shell_objects
