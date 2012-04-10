import re

import kernel.filesystem
import kernel.stream

class Shell(object):
    def __init__(self, pid, parent=None, stdin='', currentpath="/"):
        self.curpath = currentpath
        self.parent = parent
        self.pid = pid
        if self.parent:
            self.vars = self.parent.vars.copy()
            self.aliases = self.parent.aliases.copy()
        else:
            self.vars = {"PATH":"/programs"}
            self.aliases = dict()
        self.stdin = stdin
        self.stdout = kernel.stream.Stream()
        self.stderr = kernel.stream.Stream()
        self.prevcommands = []

    def get_curpath(self):
        return self.curpath

    def set_curpath(self, path):
        self.curpath = self.iabs_path(path)

    def iabs_path(self, path):
        if path[0] != '/':
            if path[0:2] == "./":
                path = path[2:]
            path = kernel.filesystem.join_path(self.curpath, path)
        return '/' + kernel.filesystem.eval_path(path)

    def irel_path(self, path, base=None):
        if base is None:
            base = self.curpath
        return kernel.filesystem.rel_path(self.iabs_path(path), self.iabs_path(base))

    def get_var(self, name):
        try:
            x = self.vars[name.group(0).lstrip("$")]
        except AttributeError:
            x = self.vars[name.lstrip("$")]
        except:
            x = ''
        return x

    def set_var(self, name, value):
        self.vars[name] = value

    def eval_input(self, string):
        #used to replace $vars
        parts = [re.sub(r"\$\w*", self.get_var, x) for x in string.split()]
        if kernel.filesystem.is_directory(self.iabs_path(parts[0])):
            print "Is a directory"
        if parts[0] in self.aliases:
            parts[0] = self.aliases[parts[0]]
        return parts[0], parts[1:] #(program, [args])

    def program_paths(self, name):
        if name[0:2] == "./":
            a = [self.iabs_path(name)]
        else:
            paths = self.get_var('PATH').split(':')
            a = [kernel.filesystem.join_path(x, name) for x in paths]
        return a

    def run_program(self, name, args):
        for x in self.program_paths(name):
            program = kernel.filesystem.open_program(x)
            if program:
                program.run(self, args)
                break
        if not program:
            print "%s: command not found" %name

    def run(self):
        running = True
        while running:
            data = raw_input("me@pyOS:%s$ "%self.curpath)
            if data:
                prgmname, args = self.eval_input(data)
                if prgmname:
                    self.run_program(prgmname, args)