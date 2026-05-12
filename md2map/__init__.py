"""md2map - マークダウンファイルを意味的単位に分割するCLIツール"""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("md2map")
except PackageNotFoundError:
    __version__ = "0.0.0"
