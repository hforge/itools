import pprint


class PathTrie:
    def __init__(self):
        self.root = {}

    def add(self, path):
        parts = self._split_path(path)
        node = self.root
        for part in parts[:-1]:
            node = node.setdefault(part, {})
            assert type(node) is dict, f'Cannot add child-path {path}'

        name = parts[-1]
        assert name not in node, f'Cannot add parent-path {path}'
        node[name] = True

    def clear(self):
        self.root = {}

    def discard(self, path):
        parts = self._split_path(path)
        node = self.root
        for part in parts[:-1]:
            if part not in node:
                return
            node = node[part]
            if type(node) is not dict:
                return

        name = parts[-1]
        if name in node:
            del node[name]

    def remove(self, path):
        parts = self._split_path(path)
        node = self.root
        for part in parts[:-1]:
            node = node[part]
            if type(node) is not dict:
                return

        name = parts[-1]
        node[name]
        del node[name]

    def __contains__(self, path):
        node = self._traverse(path)
        return node is True

    def has_subpath(self, path):
        node = self._traverse(path)
        return type(node) is dict and len(node) > 0

    def __iter__(self):
        return self._iter_nodes(self.root, [])

    def iter(self, path):
        node = self._traverse(path)
        current_path = self._split_path(path)
        return self._iter_nodes(node, current_path)

    def _iter_nodes(self, node, current_path):
        if node is True:
            yield '/'.join(current_path)
        elif type(node) is dict:
            for part, child in sorted(node.items()):
                yield from self._iter_nodes(child, current_path + [part])

    def _traverse(self, path):
        """Return the node at the given path."""
        node = self.root
        for part in self._split_path(path):
            if part not in node:
                return None
            node = node[part]

        return node

    def _split_path(self, path):
        path = path.strip('/')
        return [p for p in path.split('/') if p] if path else []


if __name__ == '__main__':
    pt = PathTrie()
#   print('' in pt)
#   print(pt.has_subpath(''))

    pt.add('a/b/c')
    pt.add('a/b/d')
    pt.add('a/x')
    pprint.pprint(pt.root)

    pt.remove('a/b')
    pprint.pprint(pt.root)

#   for x in pt.iter('a/b'):
#       print(x)

#   pt.remove('a/x')
#   pprint.pprint(pt.root)
#   pt.remove('a/x')
