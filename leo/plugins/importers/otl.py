#@+leo-ver=5-thin
#@+node:ekr.20140723122936.18150: * @file ../plugins/importers/otl.py
"""The @auto importer for vim-outline files."""
import re
from typing import Dict, List
from leo.core.leoNodes import Position, VNode
from leo.plugins.importers.linescanner import Importer
#@+others
#@+node:ekr.20161124034614.2: ** class Otl_Importer
class Otl_Importer(Importer):
    """The importer for the otl lanuage."""

    def __init__(self, importCommands, **kwargs):
        """Otl_Importer.__init__"""
        super().__init__(
            importCommands,
            language='plain',
            state_class=None,
            strict=False,
        )

    #@+others
    #@+node:ekr.20161124035243.1: *3* otl_i.gen_lines
    # Must match body pattern first.
    otl_body_pattern = re.compile(r'^: (.*)$')
    otl_node_pattern = re.compile(r'^[ ]*(\t*)(.*)$')

    def gen_lines(self, lines, parent):
        """Node generator for otl (vim-outline) mode."""
        assert parent == self.root
        # Use a dict instead of creating a new VNode slot.
        lines_dict : Dict[VNode, List[str]] = {self.root.v: []}  # Lines for each vnode.
        parents: List[Position] = [self.root]
        for line in lines:
            if not line.strip():
                continue  # New.
            m = self.otl_body_pattern.match(line)
            if m:
                parent =  parents[-1]
                lines_dict [parent.v].append(m.group(1) + '\n')
                continue
            m = self.otl_node_pattern.match(line)
            if m:
                # Cut back the stack, then allocate a new node.
                level = 1 + len(m.group(1))
                parents = parents[:level]
                self.create_placeholders(level, lines_dict, parents)
                parent =  parents[-1] if parents else self.root
                child = parent.insertAsLastChild()
                child.h = m.group(2)
                parents.append(child)
                lines_dict [child.v] = []
            else:  # pragma: no cover
                self.error(f"Bad otl line: {line!r}")
        # Add the directives.
        root_lines = lines_dict[self.root.v]
        if root_lines and not root_lines[-1].endswith('\n'):
            root_lines.append('\n')
        root_lines.extend([
            '@language otl\n',
            f"@tabwidth {self.tab_width}\n",
        ])
        # Set p.b from the lines_dict.
        for p in self.root.self_and_subtree():
            assert not p.b, repr(p.b)
            p.b = ''.join(lines_dict[p.v])
    #@+node:ekr.20220803162645.1: *3* otl.regularize_whitespace
    def regularize_whitespace(self, lines):
        """
        Otl_Importer.regularize_whitespace.

        Tabs are part of the otl format. Leave them alone.
        Convert tabs to blanks or vice versa depending on the @tabwidth in effect.
        """
        return lines
    #@-others
#@-others
importer_dict = {
    '@auto': ['@auto-otl', '@auto-vim-outline',],
    'func': Otl_Importer.do_import(),
    'extensions': ['.otl',],
}
#@@language python
#@@tabwidth -4
#@-leo
