# fse_pipeline/__init__.py
from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("fse_pipeline")
except PackageNotFoundError:
    __version__ = "development"
