import jinja2

from Questionnaire.templatetags.questionnaire_tags import (
    ContextExtension,
    MultiQuestionExtension,
    QuestionExtension,
    WhenExtension,
    _CollectMultiQuestionExtension,
    _CollectQuestionExtension,
    _PassthroughContextExtension,
    _PassthroughWhenExtension,
    _collecting_text,
    _req_collector,
    answer,
    multianswer,
    show,
    text,
)


def get_environment() -> jinja2.Environment:
    env = jinja2.Environment(
        autoescape=True,
        undefined=jinja2.Undefined,
        extensions=[WhenExtension, ContextExtension, QuestionExtension, MultiQuestionExtension],
    )
    env.globals["answer"] = answer
    env.globals["multianswer"] = multianswer
    env.globals["show"] = show
    env.globals["text"] = text
    return env


environment = get_environment()


def get_required_fields_environment() -> jinja2.Environment:
    env = jinja2.Environment(
        autoescape=True,
        undefined=jinja2.Undefined,
        extensions=[
            _PassthroughWhenExtension,
            _PassthroughContextExtension,
            _CollectQuestionExtension,
            _CollectMultiQuestionExtension,
        ],
    )
    env.globals["answer"] = lambda *a, **kw: ""
    env.globals["multianswer"] = lambda *a, **kw: ""
    env.globals["show"] = lambda *a, **kw: ""
    env.globals["text"] = _collecting_text
    return env


required_fields_env = get_required_fields_environment()


def get_required_fields(template_source: str) -> list[str]:
    """
    Return the names of all fields marked ``"required"`` in *template_source*,
    in document order.

    Handles ``{% question %}``, ``{% multiquestion %}``, and ``{{ text() }}``.
    All other constructs (``{% when %}``, ``{% context %}``, ``{{ answer() }}``,
    ``{{ multianswer() }}``, ``{{ show() }}``) are treated as no-op stubs.
    """
    _req_collector.fields = []
    try:
        required_fields_env.from_string(template_source).render()
    finally:
        result = _req_collector.fields[:]
        del _req_collector.fields
    return result
