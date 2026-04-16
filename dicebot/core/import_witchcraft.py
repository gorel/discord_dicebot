#!/usr/bin/env python3

import importlib
import pkgutil
from types import ModuleType
from typing import Dict


def _onerror(name: str) -> None:
    """Silently skip packages that cannot be imported during walk_packages."""
    pass


# From https://stackoverflow.com/a/25562415
def import_submodules(package: str, recursive: bool = False) -> Dict[str, ModuleType]:
    """Import all submodules of a module, recursively, including subpackages"""
    module = importlib.import_module(package)

    results = {}
    for _, name, is_pkg in pkgutil.walk_packages(module.__path__, onerror=_onerror):
        full_name = module.__name__ + "." + name
        try:
            results[full_name] = importlib.import_module(full_name)
        except (ModuleNotFoundError, Exception):
            pass

        if recursive and is_pkg:
            results.update(import_submodules(full_name))
    return results
