import os


def get_files_in_tree(tree='.'):
    """Return a list of all filepaths in given directory."""
    result = []
    for dirpath, _, filenames in os.walk(tree):
        for filename in filenames:
            # relpath normalizes ./foo.txt and ././foo.txt into foo.txt
            result.append(
                os.path.relpath(os.path.join(dirpath, filename), tree))
    return result
