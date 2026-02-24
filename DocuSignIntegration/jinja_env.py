import jinja2


def format_tin(value: str) -> str:
    """Split a value into groups of 3 characters separated by hyphens.

    Example: "123456789" -> "123-456-789"
    """
    s = str(value)
    return '-'.join(s[i:i + 3] for i in range(0, len(s), 3))


def get_environment() -> jinja2.Environment:
    env = jinja2.Environment(autoescape=False, undefined=jinja2.Undefined)
    env.filters['format_tin'] = format_tin
    return env


environment = get_environment()
