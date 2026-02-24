"""
Custom Jinja2 extensions and globals for questionnaire page content rendering.

Usage in a Page's Jinja2 content field
---------------------------------------

Single-choice (radio) question — standalone:

    {% question "shipping", "How would you like your order shipped?" %}
        {{ answer("standard", "Standard", "4–10 business days") }}
        {{ answer("fast",     "Fast",     "2–5 business days") }}
        {{ answer("next_day", "Next day", "1 business day") }}
    {% endquestion %}

Multiple-choice (checkbox) question — standalone:

    {% multiquestion "features", "Which features matter most to you?" %}
        {{ multianswer("speed",   "Speed",   "Fast response times") }}
        {{ multianswer("price",   "Price",   "Competitive pricing") }}
        {{ multianswer("support", "Support", "24/7 help available") }}
    {% endmultiquestion %}

Shared-scope context — conditionally show questions based on prior answers:

    {% context "pet_owner", "pet_type" %}

        {% question "pet_owner", "Do you have pets?" %}
            {{ answer("yes", "Yes") }}
            {{ answer("no",  "No") }}
        {% endquestion %}

        <div x-show="pet_owner === 'yes'" x-cloak>
            {% question "pet_type", "What kind of pet?" %}
                {{ answer("dog",   "Dog") }}
                {{ answer("cat",   "Cat") }}
                {{ answer("other", "Other") }}
            {% endquestion %}
        </div>

    {% endcontext %}

Inside ``{% context %}``, ``{% question %}`` tags bind their value directly
into the shared Alpine.js scope (no per-question ``x-data``), so field names
declared in the context tag are available as plain Alpine variables anywhere
within the block.

All globals and extensions are registered in ``Questionnaire/jinja_env.py``.
"""

import threading

from jinja2 import nodes
from jinja2.ext import Extension
from markupsafe import Markup, escape

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _js_str(value: str) -> str:
    """Escape a string for safe embedding in a JS single-quoted string literal."""
    return value.replace("\\", "\\\\").replace("'", "\\'")


def _make_badge(required) -> str:
    """
    Return the HTML badge fragment for a question label.

    ``"required"``  → red asterisk with a screen-reader label.
    ``"optional"``  → muted ``(optional)`` text.
    anything else  → empty string (no badge).
    """
    if required == "required":
        return (
            '<span class="ml-1 text-red-500" aria-hidden="true">*</span>'
            '<span class="sr-only"> (required)</span>'
        )
    if required == "optional":
        return '<span class="ml-2 text-sm font-normal text-gray-400">(optional)</span>'
    return ""


# Thread-local flag: True while rendering inside a {% context %} block.
# Jinja2 renders synchronously, so this is safe for multi-threaded Django —
# each request thread has its own local state.
_render_ctx = threading.local()


def _in_context() -> bool:
    return getattr(_render_ctx, "active", False)


# ---------------------------------------------------------------------------
# HTML skeletons — %(key)s substitution avoids f-string / Jinja2 brace
# conflicts with Alpine.js object literals  { ... }.
# ---------------------------------------------------------------------------

# --- Context wrapper --------------------------------------------------------

# %(fields_init)s  e.g.  "pet_owner": '', "pet_type": ''
_CONTEXT_TMPL = """\
<div x-data="{ %(fields_init)s }">
%(inner)s
</div>"""

# --- Single-choice (radio via @alpinejs/ui x-radio) -------------------------

# Standalone: x-data wraps both the hidden input and the x-radio group so the
# hidden input is a sibling (not a child) of x-radio. This prevents
# @alpinejs/ui from treating the hidden input as a radio child element.
_QUESTION_TMPL = """\
<div class="mb-10">
  <p class="text-base font-semibold text-gray-900 mb-4">%(label)s%(badge)s</p>
  <div x-data="{ value: '' }" class="w-full max-w-xl">
    <input type="hidden" name="%(name)s" :value="value">
    <div x-radio x-model="value">
      <label x-radio:label class="sr-only">%(label)s</label>
      <div class="flex flex-col gap-3">
%(inner)s
      </div>
    </div>
  </div>
</div>"""

# Context-mode: no x-data — binds x-radio directly into the shared parent
# scope. The hidden input is a sibling of x-radio, not a child, for the same
# reason as above.
# %(js_name)s is the raw JS identifier (field name); %(name)s is HTML-escaped.
_QUESTION_CTX_TMPL = """\
<div class="mb-10">
  <p class="text-base font-semibold text-gray-900 mb-4">%(label)s%(badge)s</p>
  <div class="w-full max-w-xl">
    <input type="hidden" name="%(name)s" :value="%(js_name)s">
    <div x-radio x-model="%(js_name)s">
      <label x-radio:label class="sr-only">%(label)s</label>
      <div class="flex flex-col gap-3">
%(inner)s
      </div>
    </div>
  </div>
</div>"""

_ANSWER_TMPL = """\
<div x-radio:option value="%(value)s"
  class="flex flex-1 cursor-pointer items-center justify-between gap-4 rounded-lg border p-4 shadow-sm transition-colors hover:bg-gray-50"
  :class="{ 'border-indigo-600 bg-indigo-50': $radioOption.isChecked, 'border-gray-200 bg-white': !$radioOption.isChecked }"
>
  <div class="flex flex-1 flex-col">
    <p x-radio:label class="font-medium text-gray-800">%(label)s</p>
    %(desc)s
  </div>
  <div class="flex h-5 w-5 shrink-0 items-center justify-center rounded-full border-2 transition-colors"
       :class="{ 'border-indigo-600 bg-indigo-600': $radioOption.isChecked, 'border-gray-300 bg-white': !$radioOption.isChecked }">
    <svg x-show="$radioOption.isChecked" class="h-3 w-3 text-white" fill="currentColor" viewBox="0 0 8 8" aria-hidden="true">
      <circle cx="4" cy="4" r="3"/>
    </svg>
  </div>
</div>"""

_ANSWER_DESC_TMPL = (
    '<p x-radio:description class="mt-1 text-sm text-gray-500">%(desc)s</p>'
)

# --- Multiple-choice (checkbox via plain Alpine.js) -------------------------

_MULTI_QUESTION_TMPL = """\
<div class="mb-10">
  <p class="text-base font-semibold text-gray-900 mb-4">%(label)s%(badge)s</p>
  <div x-data="{ values: [] }" class="w-full max-w-xl">
    <template x-for="v in values" :key="v">
      <input type="hidden" name="%(name)s" :value="v">
    </template>
    <div class="flex flex-col gap-3" role="group" aria-label="%(label)s">
%(inner)s
    </div>
  </div>
</div>"""

# %(js_value)s  — JS-escaped, used inside Alpine expressions
# %(html_value)s — HTML-escaped, used in HTML attribute values
_MULTI_ANSWER_TMPL = """\
<label
  class="flex flex-1 cursor-pointer items-center justify-between gap-4 rounded-lg border p-4 shadow-sm transition-colors hover:bg-gray-50"
  :class="{ 'border-indigo-600 bg-indigo-50': values.includes('%(js_value)s'), 'border-gray-200 bg-white': !values.includes('%(js_value)s') }"
>
  <div class="flex flex-1 flex-col">
    <span class="font-medium text-gray-800">%(label)s</span>
    %(desc)s
  </div>
  <div class="flex h-5 w-5 shrink-0 items-center justify-center rounded border-2 transition-colors"
       :class="{ 'border-indigo-600 bg-indigo-600': values.includes('%(js_value)s'), 'border-gray-300 bg-white': !values.includes('%(js_value)s') }">
    <svg x-show="values.includes('%(js_value)s')" class="h-3 w-3 text-white" fill="none"
         stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"
         viewBox="0 0 12 12" aria-hidden="true">
      <path d="M2 6l3 3 5-5"/>
    </svg>
  </div>
  <input type="checkbox" x-model="values" value="%(html_value)s" class="sr-only" aria-label="%(label)s">
</label>"""

_MULTI_ANSWER_DESC_TMPL = (
    '<span class="mt-1 text-sm text-gray-500">%(desc)s</span>'
)

# --- Free-text input --------------------------------------------------------

_TEXT_INPUT_TMPL = """\
<div class="mb-10">
  <label for="%(name)s" class="block text-base font-semibold text-gray-900 mb-2">%(label)s%(badge)s</label>
  <input type="text" id="%(name)s" name="%(name)s"
    class="w-full max-w-xl rounded-lg border border-gray-200 px-4 py-3 text-gray-800 shadow-sm placeholder:text-gray-400 focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-200 transition-colors"
    %(placeholder)s>
</div>"""

_TEXT_AREA_TMPL = """\
<div class="mb-10">
  <label for="%(name)s" class="block text-base font-semibold text-gray-900 mb-2">%(label)s%(badge)s</label>
  <textarea id="%(name)s" name="%(name)s" rows="%(rows)s"
    class="w-full max-w-xl rounded-lg border border-gray-200 px-4 py-3 text-gray-800 shadow-sm placeholder:text-gray-400 focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-200 transition-colors resize-y"
    %(placeholder)s></textarea>
</div>"""


# --- Conditional visibility -------------------------------------------------

_WHEN_TMPL = """\
<div x-show="%(var)s === '%(js_value)s'" x-cloak
     x-transition:enter="transition ease-out duration-200"
     x-transition:enter-start="opacity-0 translate-y-2"
     x-transition:enter-end="opacity-100 translate-y-0"
     x-transition:leave="transition ease-in duration-150"
     x-transition:leave-start="opacity-100 translate-y-0"
     x-transition:leave-end="opacity-0 translate-y-2">
%(inner)s
</div>"""


# ---------------------------------------------------------------------------
# Extensions
# ---------------------------------------------------------------------------

class WhenExtension(Extension):
    """
    Jinja2 extension that wraps content in an Alpine.js ``x-show`` block,
    making it visible only when a named variable equals a given value.

    Syntax::

        {% when "var_name", "expected_value" %}
            ...content shown when var_name === 'expected_value'...
        {% endwhen %}

    Intended for use inside a ``{% context %}`` block where the variable is
    declared in the shared Alpine scope::

        {% context "mood", "follow_up" %}

            {% question "mood", "How are you feeling?" %}
                {{ answer("happy", "Happy") }}
                {{ answer("sad",   "Sad") }}
            {% endquestion %}

            {% when "mood", "sad" %}
                {% question "follow_up", "What's troubling you?" %}
                    {{ answer("work",  "Work stress") }}
                    {{ answer("other", "Other") }}
                {% endquestion %}
            {% endwhen %}

        {% endcontext %}
    """

    tags = {"when"}

    def parse(self, parser):
        lineno = next(parser.stream).lineno
        var_node = parser.parse_expression()
        parser.stream.expect("comma")
        value_node = parser.parse_expression()
        body = parser.parse_statements(("name:endwhen",), drop_needle=True)
        return nodes.CallBlock(
            self.call_method("_render", [var_node, value_node]),
            [], [], body,
        ).set_lineno(lineno)

    @staticmethod
    def _render(var: str, value: str, caller) -> str:
        return Markup(
            _WHEN_TMPL % {
                "var": _js_str(var),
                "js_value": _js_str(value),
                "inner": caller(),
            }
        )


class ContextExtension(Extension):
    """
    Jinja2 extension that creates a shared Alpine.js ``x-data`` scope for a
    group of questions, enabling one question's answer to drive ``x-show``,
    ``x-if``, or ``:class`` on subsequent questions.

    Syntax::

        {% context "field_a", "field_b", ... %}
            ...
        {% endcontext %}

    Each named field is initialised as an empty string in the Alpine data
    object.  ``{% question %}`` blocks inside the context automatically bind
    into this scope instead of creating their own isolated ``x-data``.

    Use plain Alpine directives for conditional visibility::

        <div x-show="field_a === 'yes'" x-cloak>
            {% question "field_b", "Follow-up question?" %}
                ...
            {% endquestion %}
        </div>

    ``x-cloak`` requires the rule ``[x-cloak] { display: none }`` in your CSS
    (or Tailwind's ``hidden`` utility) to prevent a flash of content on load.
    """

    tags = {"context"}

    def parse(self, parser):
        lineno = next(parser.stream).lineno

        # Collect comma-separated field name expressions until block_end.
        field_nodes: list[nodes.Expr] = []
        while not parser.stream.current.test("block_end"):
            if field_nodes:
                parser.stream.expect("comma")
            field_nodes.append(parser.parse_expression())

        # Pack them into a single List node so _render receives one argument.
        fields_list_node = nodes.List(field_nodes, lineno=lineno)
        body = parser.parse_statements(("name:endcontext",), drop_needle=True)

        return nodes.CallBlock(
            self.call_method("_render", [fields_list_node]),
            [], [], body,
        ).set_lineno(lineno)

    @staticmethod
    def _render(fields: list[str], caller) -> str:
        _render_ctx.active = True
        try:
            inner = caller()
        finally:
            _render_ctx.active = False

        # Build Alpine x-data init string: field_a: '', field_b: ''
        # Keys must be unquoted identifiers — double quotes inside an HTML
        # attribute delimited by double quotes would truncate the attribute value.
        fields_init = ", ".join(f"{f}: ''" for f in fields)
        return Markup(
            _CONTEXT_TMPL % {
                "fields_init": fields_init,
                "inner": inner,
            }
        )


class QuestionExtension(Extension):
    """
    Jinja2 extension that adds the ``{% question %}`` block tag.

    Standalone syntax (creates its own Alpine scope)::

        {% question "field_name", "Question text?" %}
        {% question "field_name", "Question text?", "required" %}
        {% question "field_name", "Question text?", "optional" %}

            {{ answer("value_a", "Option A") }}
            {{ answer("value_b", "Option B", "With optional description") }}
        {% endquestion %}

    When nested inside ``{% context %}``, the question binds into the shared
    scope automatically — no change to the tag syntax is required.
    """

    tags = {"question"}

    def parse(self, parser):
        lineno = next(parser.stream).lineno
        name_node = parser.parse_expression()
        parser.stream.expect("comma")
        label_node = parser.parse_expression()
        if parser.stream.current.test("comma"):
            next(parser.stream)
            required_node = parser.parse_expression()
        else:
            required_node = nodes.Const(None)
        body = parser.parse_statements(("name:endquestion",), drop_needle=True)
        return nodes.CallBlock(
            self.call_method("_render", [name_node, label_node, required_node]),
            [], [], body,
        ).set_lineno(lineno)

    @staticmethod
    def _render(name: str, label: str, required, caller) -> str:
        inner = caller()
        badge = _make_badge(required)
        if _in_context():
            return Markup(
                _QUESTION_CTX_TMPL % {
                    "js_name": _js_str(name),
                    "name": escape(name),
                    "label": escape(label),
                    "badge": badge,
                    "inner": inner,
                }
            )
        return Markup(
            _QUESTION_TMPL % {
                "name": escape(name),
                "label": escape(label),
                "badge": badge,
                "inner": inner,
            }
        )


class MultiQuestionExtension(Extension):
    """
    Jinja2 extension that adds the ``{% multiquestion %}`` block tag for
    questions that accept multiple answers (checkboxes).

    Syntax::

        {% multiquestion "field_name", "Question text?" %}
            {{ multianswer("value_a", "Option A") }}
            {{ multianswer("value_b", "Option B", "With optional description") }}
        {% endmultiquestion %}

    Selected values are submitted as multiple POST values under the same
    field name. In the view, retrieve them with::

        request.POST.getlist("field_name")

    Alpine.js manages the selected state as an array. A ``<template x-for>``
    emits a hidden ``<input>`` for each selected value, so no JavaScript is
    needed at submit time.

    Note: ``{% multiquestion %}`` always owns its own ``x-data`` even inside
    a ``{% context %}`` block, because it manages a list rather than a scalar.
    Wrap it in a ``<div x-show="...">`` to conditionally hide it based on
    other context fields.
    """

    tags = {"multiquestion"}

    def parse(self, parser):
        lineno = next(parser.stream).lineno
        name_node = parser.parse_expression()
        parser.stream.expect("comma")
        label_node = parser.parse_expression()
        if parser.stream.current.test("comma"):
            next(parser.stream)
            required_node = parser.parse_expression()
        else:
            required_node = nodes.Const(None)
        body = parser.parse_statements(("name:endmultiquestion",), drop_needle=True)
        return nodes.CallBlock(
            self.call_method("_render", [name_node, label_node, required_node]),
            [], [], body,
        ).set_lineno(lineno)

    @staticmethod
    def _render(name: str, label: str, required, caller) -> str:
        inner = caller()
        return Markup(
            _MULTI_QUESTION_TMPL % {
                "name": escape(name),
                "label": escape(label),
                "badge": _make_badge(required),
                "inner": inner,
            }
        )


# ---------------------------------------------------------------------------
# Global callables
# ---------------------------------------------------------------------------

def answer(value: str, label: str, description: str = "") -> Markup:
    """
    Render a single radio option for use inside ``{% question %}``.

    Args:
        value:       The form value submitted when this option is chosen.
        label:       Primary display text.
        description: Optional secondary text shown beneath the label.
    """
    desc_html = (
        _ANSWER_DESC_TMPL % {"desc": escape(description)}
        if description
        else ""
    )
    return Markup(
        _ANSWER_TMPL % {
            "value": escape(value),
            "label": escape(label),
            "desc": desc_html,
        }
    )


def multianswer(value: str, label: str, description: str = "") -> Markup:
    """
    Render a single checkbox option for use inside ``{% multiquestion %}``.

    Args:
        value:       The form value included in the POST list when selected.
        label:       Primary display text.
        description: Optional secondary text shown beneath the label.
    """
    desc_html = (
        _MULTI_ANSWER_DESC_TMPL % {"desc": escape(description)}
        if description
        else ""
    )
    return Markup(
        _MULTI_ANSWER_TMPL % {
            "js_value": _js_str(value),
            "html_value": escape(value),
            "label": escape(label),
            "desc": desc_html,
        }
    )


def text(
    name: str,
    label: str,
    required=None,
    *,
    placeholder: str = "",
    multiline: bool = False,
    rows: int = 4,
) -> Markup:
    """
    Render a styled free-text input field.

    Args:
        name:        The form field name submitted in the POST body.
        label:       The visible label for the field.
        required:    ``"required"`` shows a red ``*``; ``"optional"`` shows a
                     muted badge; ``None`` (default) shows nothing.
        placeholder: Optional placeholder text for the input.
        multiline:   If ``True``, renders a ``<textarea>`` instead of an
                     ``<input type="text">``.
        rows:        Number of visible rows for a ``multiline`` textarea
                     (default ``4``).

    Examples::

        {{ text("full_name", "Full name", "required") }}
        {{ text("bio", "Short bio", "optional", multiline=true, rows=6) }}
        {{ text("notes", "Extra notes", placeholder="Anything else?") }}
    """
    ph = f'placeholder="{escape(placeholder)}"' if placeholder else ""
    tmpl = _TEXT_AREA_TMPL if multiline else _TEXT_INPUT_TMPL
    return Markup(
        tmpl % {
            "name": escape(name),
            "label": escape(label),
            "badge": _make_badge(required),
            "placeholder": ph,
            "rows": int(rows),
        }
    )


# ---------------------------------------------------------------------------
# Required-fields collection — used by required_fields_env in jinja_env.py
# ---------------------------------------------------------------------------

_req_collector = threading.local()


def _collect_if_required(name: str, required) -> None:
    """Append *name* to the active bucket when required == 'required'."""
    bucket = getattr(_req_collector, "fields", None)
    if required == "required" and bucket is not None:
        bucket.append(name)


class _CollectQuestionExtension(QuestionExtension):
    """Collects required field names; emits no HTML."""

    @staticmethod
    def _render(name: str, label: str, required, caller) -> str:
        _collect_if_required(name, required)
        caller()
        return Markup("")


class _CollectMultiQuestionExtension(MultiQuestionExtension):
    """Collects required field names; emits no HTML."""

    @staticmethod
    def _render(name: str, label: str, required, caller) -> str:
        _collect_if_required(name, required)
        caller()
        return Markup("")


class _PassthroughContextExtension(ContextExtension):
    """Processes the context body without building Alpine HTML."""

    @staticmethod
    def _render(fields: list[str], caller) -> str:
        _render_ctx.active = True
        try:
            caller()
        finally:
            _render_ctx.active = False
        return Markup("")


class _PassthroughWhenExtension(WhenExtension):
    """Processes the when body without wrapping in x-show."""

    @staticmethod
    def _render(var: str, value: str, caller) -> str:
        caller()
        return Markup("")


def _collecting_text(
    name: str,
    label: str,
    required=None,
    *,
    placeholder: str = "",
    multiline: bool = False,
    rows: int = 4,
) -> Markup:
    """Stub text() that only records required fields, emits no HTML."""
    _collect_if_required(name, required)
    return Markup("")


def show(var_name: str) -> Markup:
    """
    Render a ``<span>`` that displays an Alpine.js variable reactively.

    Args:
        var_name: The name of the Alpine variable to display.

    Example::

        {{ show("mood") }}  →  <span x-text="mood"></span>
    """
    return Markup(f'<span x-text="{_js_str(var_name)}"></span>')
