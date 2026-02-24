import jinja2

from Questionnaire.templatetags.questionnaire_tags import (
    ContextExtension,
    MultiQuestionExtension,
    QuestionExtension,
    WhenExtension,
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
