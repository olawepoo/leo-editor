# -*- coding: utf-8 -*-
#@+leo-ver=5-thin
#@+node:ekr.20201129023817.1: * @file leoTest2.py
#@@first
"""
Support for Leo's new unit tests, contained in leo/unittests/test_*.py.

These tests are intended to be run by unittest or pytest from the command line.

This file also contains two classes that convert nodes in unitTest.leo to
tests in leo/unittest. Eventually these classes will move to scripts.leo.
"""

import sys
import textwrap
import unittest

#@+others
#@+node:ekr.20201129132455.1: ** Top-level functions...
#@+node:ekr.20201130195111.1: *3* function: create_app
def create_app():
    """
    Create the Leo application, g.app, the Gui, g.app.gui, and a commander.
    
    This method is expensive (about 1 sec) only the first time it is called.
    
    Thereafter, recreating g.app, g.app.gui, and new commands is fast.
    """
    # t1 = time.process_time()
    from leo.core import leoGlobals as g
    from leo.core import leoApp
    g.app = leoApp.LeoApp()  # Do this first, to avoid circular dependencies.
    from leo.core import leoConfig
    from leo.core import leoNodes
    from leo.core import leoCommands
    from leo.core import leoGui
    # t2 = time.process_time()
    g.app.recentFilesManager = leoApp.RecentFilesManager()
    g.app.loadManager = leoApp.LoadManager()
    g.app.loadManager.computeStandardDirectories()
    if not g.app.setLeoID(useDialog=False, verbose=True):
        raise ValueError("unable to set LeoID.")
    g.app.nodeIndices = leoNodes.NodeIndices(g.app.leoID)
    g.app.config = leoConfig.GlobalConfigManager()
    g.app.db = g.TracingNullObject('g.app.db')
    g.app.pluginsController = g.NullObject('g.app.pluginsController')
    g.app.commander_cacher = g.NullObject('g.app.commander_cacher')
    g.app.gui = leoGui.NullGui()
    # t3 = time.process_time()
    #
    # Create a dummy commander, to do the imports in c.initObjects.
    c = leoCommands.Commands(fileName=None, gui=g.app.gui)
    # t4 = time.process_time()
    # if t4 - t3 > 0.1:
        # print('create_app\n'
            # f"  imports: {(t2-t1):.3f}\n"
            # f"      gui: {(t3-t2):.3f}\n"
            # f"commander: {(t4-t2):.3f}\n"
            # f"    total: {(t4-t1):.3f}\n")
    return c
#@+node:ekr.20210828111901.1: *3* function: create_outline
def create_outline(c, s):
    """
    Replace all nodes of c with the nodes formed by string s, copied to the clipboard.
    """
    s2 = textwrap.dedent(s.strip() + '\n')
    # g.printObj(g.splitLines(s2))
    p = c.fileCommands.getLeoOutlineFromClipboard(s2)
    unittest.TestCase().assertTrue(p)
    return c
#@+node:ekr.20201130074836.1: *3* function: convert_leoEditCommands_tests
def convert_leoEditCommands_tests(c, root, target):
    """
    Convert @test nodes to new-style tests.
    
    root:   A node containing (a copy of) tests from unitTest.leo.
    target: A node whose children will be the resulting tests.
            These nodes can then be copied to be children of a test class.
    """
    if not root or not target:
        print('Error: root and target nodes must be top-level nodes.')
        return
    # Be safe.
    if target.hasChildren():
        print('Please delete children of ', target.h)
        return
    converter = ConvertEditCommandsTests()
    count = 0
    for p in root.subtree():
        if p.h.startswith('@test') and 'runEditCommandTest' in p.b:
            converter.convert(p, target)
            count += 1
    c.redraw()
    print(f"converted {count} @test nodes")
#@+node:ekr.20201201144934.1: *3* function: dump_leo_modules
def dump_leo_modules():

    core = [z for z in sys.modules if z.startswith('leo.core')]
    commands = [z for z in sys.modules if z.startswith('leo.commands')]
    plugins = [z for z in sys.modules if z.startswith('leo.plugins')]

    print(f"{len(core)} leo.core modules...\n")
    for key in sorted(core):
        print(key)
    print(f"\n{len(commands)} leo.command modules...\n")
    for key in sorted(commands):
        print(key)
    print(f"\n{len(plugins)} leo.plugins modules...\n")
    for key in sorted(plugins):
        print(key)
#@+node:ekr.20201202083003.1: ** class ConvertTests
class ConvertTests:
    """
    A class that converts @test nodes to proper unit tests.
    
    Subclasses specialize the convert method.
    
    These scripts know nothing about the unit tests they create. They just
    pass the data from the old tests to the new tests using args in the
    run_test method.
    """
    #@+others
    #@+node:ekr.20201130075024.2: *3* ConvertTests.body
    def body(self, after_p, after_sel, before_p, before_sel, command_name):
        """Return the body of the test"""
        real_command_name = command_name.split(' ')[0]
        sel11, sel12 = before_sel.split(',')
        sel21, sel22 = after_sel.split(',')
        delim = "'''" if '"""' in before_p.b else '"""'
        return (
            f"def test_{self.function_name(command_name)}(self):\n"
            f'    """Test case for {command_name}"""\n'
            f'    before_b = {delim}\\\n'
            f"{before_p.b}"
            f'{delim}\n'
            f'    after_b = {delim}\\\n'
            f"{after_p.b}"
            f'{delim}\n'
            f"    self.run_test(\n"
            f"        before_b=before_b,\n"
            f"        after_b=after_b,\n"
            f'        before_sel=("{sel11}", "{sel12}"),\n'
            f'        after_sel=("{sel21}", "{sel22}"),\n'
            f'        command_name="{real_command_name}",\n'
            f"    )\n"
        )
    #@+node:ekr.20201130075024.3: *3* ConvertTests.class_name
    def class_name(self, command_name):
        """Convert the command name to a class name."""
        # This method is not used.
        result = []
        parts = command_name.split('-')
        for part in parts:
            s = part.replace('(', '').replace(')', '')
            inner_parts = s.split(' ')
            result.append(''.join([z.capitalize() for z in inner_parts]))
        return ''.join(result)
    #@+node:ekr.20201202083708.1: *3* ConvertTests.convert
    def convert(self, p, target):
        """
        Convert one @test node, creating a new node as the last child of target.
        
        Must be overridden in subclasses.
        """
        print('ConvertTests.convert: Must be overridden')
    #@+node:ekr.20201130075024.5: *3* ConvertTests.function_name
    def function_name(self, command_name):
        """Convert a command name into a test function."""
        result = []
        parts = command_name.split('-')
        for part in parts:
            s = part.replace('(', '').replace(')', '')
            inner_parts = s.split(' ')
            result.append('_'.join(inner_parts))
        return '_'.join(result)
    #@-others
#@+node:ekr.20201202083553.1: ** class ConvertEditCommandsTests (ConvertTests)
class ConvertEditCommandsTests(ConvertTests):

    #@+others
    #@+node:ekr.20201130075024.4: *3* ConvertEditCommandsTests.convert
    def convert(self, p, target):
        """Convert one @test node, creating a new node."""
        after_p, before_p = None, None
        after_sel, before_sel = None, None
        assert p.h.startswith('@test')
        command_name = p.h[len('@test') :].strip()
        for child in p.children():
            if child.h.startswith('after'):
                after_p = child.copy()
                after_sel = child.h[len('after') :].strip()
                after_sel = after_sel.replace('sel=', '').strip()
            elif child.h.startswith('before'):
                before_p = child.copy()
                before_sel = child.h[len('before') :].strip()
                before_sel = before_sel.replace('sel=', '').strip()
        assert before_p and after_p
        assert before_sel and after_sel
        new_child = target.insertAsLastChild()
        new_child.h = command_name
        new_child.b = self.body(after_p, after_sel, before_p, before_sel, command_name)

    #@-others
#@-others
#@-leo
