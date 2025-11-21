from importlib.resources import files


def get_schema_path(name: str):
    return files(__package__) / name
