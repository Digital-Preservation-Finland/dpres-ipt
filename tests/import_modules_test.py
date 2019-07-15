"""Test that all modules are imported without errors.

This test improves coverage reporting by importing every module in the project.
Coverage calculates line coverage only for imported modules, so untested
modules would not be included in the coverage report.

"""

import os
import pytest
from importlib import import_module


@pytest.mark.parametrize('package', ['ipt'])
def test_import_modules(package):
    """Import all modules from project source directory"""

    project_path = os.path.abspath(os.path.join(
        os.path.dirname(__file__), '..'))

    package_path = os.path.join(project_path, package)

    import_count = 0
    for root, _, files in os.walk(package_path):

        for filename in files:
            if not filename.endswith('.py'):
                continue
            module_name = _provide_module_name(project_path, root, filename)
            try:
                import_module(module_name)
                if filename == '__init__.py':
                    continue
                import_count += 1
            except ImportError:
                pytest.fail('Failed loading module %s' % module_name)

    assert import_count > 1


def _provide_module_name(project_path, root, filename):
    module_name = os.path.relpath(
        os.path.join(root, filename), project_path)
    module_name = module_name.replace(
        '/__init__.py', '').replace('.py', '').replace('/', '.')
    return module_name
