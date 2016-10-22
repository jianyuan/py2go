import ast
from contextlib import contextmanager
from functools import wraps

def debug(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        ret = f(*args, **kwargs)
        print(f.__name__, args, kwargs, ret)
        return ret
    return wrapped


@contextmanager
def stack(stack, item):
    try:
        stack.append(item)
        yield
    finally:
        stack.pop()


class GoTranspiler(ast.NodeVisitor):

    def __init__(self):
        self.stack_FunctionDef = []

    def generic_visit(self, node):
        return '// UNSUPPORTED => ' + ast.dump(node)

    def visit_Module(self, node):
        return '\n'.join(filter(None, map(self.visit, node.body)))

    # Literals

    def visit_Num(self, node):
        return str(node.n)

    def visit_Str(self, node):
        s = node.s.replace('"', '\\"')
        return '"' + s + '"'

    def visit_Bytes(self, node):
        s = ', '.join('0x{:02x}'.format(b) for b in node.s)
        return '[]byte{' + s + '}'

    def visit_List(self, node):
        # TODO: check node.ctx
        s = ', '.join(self.visit(e) for e in node.elts)
        return '[]interface{}{' + s + '}'

    # def visit_Tuple(self, node):
    #     return

    # def visit_Set(self, node):
    #     return

    def visit_Dict(self, node):
        s = ', '.join(
            self.visit(k) + ': ' + self.visit(v)
            for (k, v) in zip(node.keys, node.values)
        )
        return 'map[interface{}]interface{}{' + s + '}'

    # def visit_Ellipsis(self, node):
    #     return

    def visit_NameConstant(self, node):
        if node.value is True:
            return 'true'
        elif node.value is False:
            return 'false'
        elif node.value is None:
            return 'nil'
        assert False

    # Variables

    def visit_Name(self, node):
        return node.id

    # Expressions

    def visit_Expr(self, node):
        return self.visit(node.value)

    def visit_BinOp(self, node):
        left = self.visit(node.left)
        op = self.visit(node.op)
        right = self.visit(node.right)
        return '{} {} {}'.format(left, op, right)

    def visit_Add(self, node):
        return '+'

    def visit_Sub(self, node):
        return '-'

    def visit_Mult(self, node):
        return '*'

    def visit_Div(self, node):
        return '/'

    # def visit_FloorDiv(self, node):
    #     return

    def visit_Mod(self, node):
        return '%'

    def visit_Call(self, node):
        func = self.visit(node.func)
        args = map(self.visit, node.args)
        return '{}({})'.format(func, ', '.join(args))

    # Statements

    def visit_Assign(self, node):
        # TODO: support more targets
        assert len(node.targets) == 1

        target = self.visit(node.targets[0])
        value = self.visit(node.value)

        return 'var {} = {}'.format(target, value)

    # Function and class definitions

    def visit_FunctionDef(self, node):
        args = self.visit(node.args)

        if node.returns is None:
            returns = ''
        else:
            returns = ' ' + self.visit(node.returns)

        lines = []

        if self.stack_FunctionDef:
            lines.append('var ' + node.name + ' = func(' + args + ')' + returns + ' {')
        else:
            lines.append('func ' + node.name + '(' + args + ')' + returns + ' {')

        with stack(self.stack_FunctionDef, node):
            lines.extend(
                '\n'.join('\t' + line for line in self.visit(n).splitlines())
                for n in node.body
            )

        lines.append('}')
        return '\n'.join(lines)

    def visit_arguments(self, node):
        return ', '.join(map(self.visit_arg, node.args))

    def visit_arg(self, node):
        if node.annotation:
            annotation = self.visit(node.annotation)
        else:
            annotation = 'interface{}'
        return node.arg + ' ' + annotation

    def visit_Return(self, node):
        return 'return ' + self.visit(node.value)
