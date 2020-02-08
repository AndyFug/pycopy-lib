# This file is part of the standard library of Pycopy project, minimalist
# and lightweight Python implementation.
#
# https://github.com/pfalcon/pycopy
# https://github.com/pfalcon/pycopy-lib
#
# The MIT License (MIT)
#
# Copyright (c) 2019 Paul Sokolovsky
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

import uio


class YamlParser:

    def __init__(self, f):
        self.f = f
        self.l = None

    def readline(self):
        if self.l is not None:
            l = self.l
            self.l = None
            return l
        return self.f.readline()

    def unreadline(self, l):
#        print("-unread:", l)
        assert self.l is None
        self.l = l

    @staticmethod
    def calc_indent(l):
        indent = 0
        while l[indent] == " ":
            indent += 1
        return indent, l[indent:]

    def detect_block_type(self):
        l = self.readline()
        self.unreadline(l)
        indent, subl = self.calc_indent(l)
        if subl.startswith("- "):
            return list
        else:
            return dict

    def parse_str(self, l, until):
        if l[0] in ("'", '"'):
            sep = l[0]
            i = 1
            while True:
                if i >= len(l):
                    assert 0
                if l[i] == sep:
                    break
                i += 1
            return l[1:i], l[i + 1:]
        else:
            if until == "":
                i = len(l)
            else:
                i = l.index(until)
            return l[:i], l[i:]

    def parse_flow(self, l):
        if l.startswith("["):
            rbuf = uio.StringIO(l)
            rbuf.read(1)
            res = []
            ident = ""
            while True:
                c = rbuf.read(1)
                if not c:
                    assert False, "Unexpected end if line"
                if c == "]":
                    res.append(ident.strip())
                    break
                if c == ",":
                    res.append(ident.strip())
                    ident = ""
                    continue
                ident += c
            rest = rbuf.read().strip()
            assert rest == ""
            return res, ""
        elif l.startswith("{"):
            raise NotImplementedError
        else:
            return self.parse_str(l, "")

    def parse_block(self, target_indent):
        res = self.detect_block_type()()
        while True:
            l = self.readline()
#            print("*", l)
            if not l:
                return res
            indent, subl = self.calc_indent(l)
            if indent != target_indent:
                self.unreadline(l)
                return res

            subl = subl.rstrip()
            if isinstance(res, list):
                if subl.startswith("- "):
                    res.append(subl[2:])
                else:
                    self.unreadline(l)
                    return res
            elif subl.endswith(":"):
                nextl = self.readline()
                nexti, _ = self.calc_indent(nextl)
                self.unreadline(nextl)
                subobj = self.parse_block(nexti)
                k, rest = self.parse_str(subl, ":")
                assert rest == ":", rest
                res[k] = subobj
            else:
                k, rest = self.parse_str(subl, ":")
                assert rest[0] == ":"
                rest = rest[1:].strip()
                v, rest = self.parse_flow(rest)
                res[k] = v
                assert rest == ""

    def parse(self):
        return self.parse_block(0)


def dump(data, stream, indent=0):
    def do_indent(indent):
        stream.write("  " * indent)

    if isinstance(data, list):
        for i in data:
            do_indent(indent - 1)
            stream.write("- ")
            dump(i, stream, indent + 1)
    elif isinstance(data, dict):
        for k, v in data.items():
            do_indent(indent)
            stream.write(str(k))
            if isinstance(v, (list, dict)):
                stream.write(":\n")
                dump(v, stream, indent + 1)
            else:
                stream.write(": ")
                dump(v, stream, indent + 1)
    else:
        stream.write(str(data))
        stream.write("\n")