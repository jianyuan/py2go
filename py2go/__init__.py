import ast
import inspect
from functools import wraps

import transpiler
from astpp import parseprint


def go(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        source = inspect.getsource(f)
        filename = inspect.getsourcefile(f)

        print('==> source')
        print(source.strip())
        print()

        tree = ast.parse(source, filename=filename)
        print('==> tree')
        parseprint(tree)
        print()

        print('==> transpile')
        out = transpiler.GoTranspiler().visit(tree)
        print(out)
        print()

        # TODO actually run the transpiled version of this function
        return f(*args, **kwargs)

    return wrapper


@go
def test(a: int, b: int) -> int:
    c = a + b + 1
    return c


def main():
    print(test(1, 2))


if __name__ == '__main__':
    main()
