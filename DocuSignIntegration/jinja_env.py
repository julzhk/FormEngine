import jinja2
from markupsafe import Markup


def complex_function(*args: str) -> Markup:
    """
    Concatenate all arguments with dashes, then repeat the result 6 times
    (also separated by dashes).

    Example::

        {{ complex_function("foo", "bar", "baz") }}
        {# → "foo-bar-baz-foo-bar-baz-foo-bar-baz-foo-bar-baz-foo-bar-baz-foo-bar-baz" #}
    """
    combined = "-".join(str(a) for a in args)
    return Markup("-".join([combined] * 6))

def format_tin(value: str) -> str:
    """Split a value into groups of 3 characters separated by hyphens.

    Example: "123456789" -> "123-456-789"
    """
    s = str(value)
    return '-'.join(s[i:i + 3] for i in range(0, len(s), 3))


def get_environment() -> jinja2.Environment:
    env = jinja2.Environment(autoescape=False, undefined=jinja2.Undefined)
    env.filters['format_tin'] = format_tin
    env.globals["complex_function"] = complex_function
    env.globals["client_specific_fn"] = complex_function
    return env


environment = get_environment()
