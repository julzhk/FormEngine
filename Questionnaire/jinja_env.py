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
    _errors_ctx,
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


def render_page(
    template_source: str,
    errors: list[str] | None = None,
    error_messages: dict[str, str] | None = None,
    **context,
) -> str:
    """
    Render a page template, highlighting any fields listed in *errors*.

    *error_messages* maps field names to custom validation messages.
    Fields without an entry fall back to "This field is required."
    """
    _errors_ctx.fields = set(errors or [])
    _errors_ctx.messages = error_messages or {}
    try:
        return environment.from_string(template_source).render(**context)
    finally:
        _errors_ctx.fields = set()
        _errors_ctx.messages = {}


def get_field_validators(template_source: str) -> dict[str, list[str]]:
    """
    Return ``{field_name: [validators]}`` for every field that declares
    validators in *template_source*.

    Handles ``{% question %}``, ``{% multiquestion %}``, and ``{{ text() }}``.
    """
    _req_collector.fields = {}
    try:
        required_fields_env.from_string(template_source).render()
    finally:
        result = dict(_req_collector.fields)
        del _req_collector.fields
    return result


