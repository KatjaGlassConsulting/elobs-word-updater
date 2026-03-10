from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("elobs-word-updater")
except PackageNotFoundError:
    __version__ = "unknown"
