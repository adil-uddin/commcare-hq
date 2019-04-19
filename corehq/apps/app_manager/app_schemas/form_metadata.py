from __future__ import absolute_import, unicode_literals

from collections import defaultdict

import six

from corehq.apps.app_manager.app_schemas.app_case_metadata import (
    AppCaseMetadata,
    LoadSaveProperty,
    FormQuestionResponse,
)
from corehq.apps.app_manager.exceptions import XFormException

from jsonobject import (
    BooleanProperty,
    DictProperty,
    JsonObject,
    ListProperty,
    ObjectProperty,
    StringProperty,
)

REMOVED = 'removed'
ADDED = 'added'
CHANGED = 'changed'

DIFF_STATES = (REMOVED, ADDED, CHANGED)

QUESTION_ATTRIBUTES = (
    'label', 'type', 'value', 'options', 'calculate', 'relevant',
    'required', 'comment', 'setvalue', 'constraint'
)

FORM_ATTRIBUTES = (
    'name', 'short_comment', 'form_filter'
)

MODULE_ATTRIBUTES = (
    'name', 'short_comment', 'module_filter'
)


class _QuestionDiff(JsonObject):
    question = StringProperty(choices=(ADDED, REMOVED))
    label = StringProperty(choices=DIFF_STATES)
    type = StringProperty(choices=DIFF_STATES)
    value = StringProperty(choices=DIFF_STATES)
    calculate = StringProperty(choices=DIFF_STATES)
    relevant = StringProperty(choices=DIFF_STATES)
    required = StringProperty(choices=DIFF_STATES)
    comment = StringProperty(choices=DIFF_STATES)
    setvalue = StringProperty(choices=DIFF_STATES)
    constraint = StringProperty(choices=DIFF_STATES)
    options = DictProperty()    # {option: state}


class _FormDiff(JsonObject):
    form = StringProperty(choices=(ADDED, REMOVED))
    name = StringProperty(choices=DIFF_STATES)
    short_comment = StringProperty(choices=DIFF_STATES)
    form_filter = StringProperty(choices=DIFF_STATES)


class _ModuleDiff(JsonObject):
    module = StringProperty(choices=(ADDED, REMOVED))
    name = StringProperty(choices=DIFF_STATES)
    short_comment = StringProperty(choices=DIFF_STATES)
    module_filter = StringProperty(choices=DIFF_STATES)


class _FormMetadataQuestion(FormQuestionResponse):
    load_properties = ListProperty(LoadSaveProperty)
    save_properties = ListProperty(LoadSaveProperty)
    changes = ObjectProperty(_QuestionDiff)


class _FormMetadata(JsonObject):
    id = StringProperty()
    name = DictProperty()
    short_comment = StringProperty()
    action_type = StringProperty()
    form_filter = StringProperty()
    questions = ListProperty(_FormMetadataQuestion)
    error = DictProperty()
    changes = ObjectProperty(_FormDiff)


class _ModuleMetadata(JsonObject):
    id = StringProperty()
    name = DictProperty()
    short_comment = StringProperty()
    module_type = StringProperty()
    is_surveys = BooleanProperty()
    module_filter = StringProperty()
    forms = ListProperty(_FormMetadata)
    changes = ObjectProperty(_ModuleDiff)


class _AppSummaryFormDataGenerator(object):
    def __init__(self, domain, app, include_shadow_forms=True):
        self.domain = domain
        self.app = app
        self.include_shadow_forms = include_shadow_forms

        self.errors = []

        self._seen_save_to_case = defaultdict(list)
        try:
            self._case_meta = self.app.get_case_metadata()
        except XFormException:
            self._case_meta = AppCaseMetadata()

    def generate(self):
        return [self._compile_module(module) for module in self.app.get_modules()], self.errors

    def _compile_module(self, module):
        return _ModuleMetadata(**{
            'id': module.unique_id,
            'name': module.name,
            'short_comment': module.short_comment,
            'module_type': module.module_type,
            'is_surveys': module.is_surveys,
            'module_filter': module.module_filter,
            'forms': [self._compile_form(form) for form in self._get_pertinent_forms(module)],
        })

    def _get_pertinent_forms(self, module):
        from corehq.apps.app_manager.models import ShadowForm
        if not self.include_shadow_forms:
            return [form for form in module.get_forms() if not isinstance(form, ShadowForm)]
        return module.get_forms()

    def _compile_form(self, form):
        form_meta = _FormMetadata(**{
            'id': form.unique_id,
            'name': form.name,
            'short_comment': form.short_comment,
            'action_type': form.get_action_type(),
            'form_filter': form.form_filter,
        })
        try:
            form_meta.questions = [
                question
                for raw_question in form.get_questions(self.app.langs, include_triggers=True,
                                                       include_groups=True, include_translations=True)
                for question in self._get_question(form.unique_id, raw_question)
            ]
        except XFormException as exception:
            form_meta.error = {
                'details': six.text_type(exception),
            }
            self.errors.append(form_meta)
        return form_meta

    def _get_question(self, form_unique_id, question):
        if self._needs_save_to_case_root_node(question, form_unique_id):
            yield self._save_to_case_root_node(form_unique_id, question)
        yield self._serialized_question(form_unique_id, question)

    def _needs_save_to_case_root_node(self, question, form_unique_id):
        return (
            self._is_save_to_case(question)
            and self._save_to_case_root_path(question) not in self._seen_save_to_case[form_unique_id]
        )

    @staticmethod
    def _is_save_to_case(question):
        return '/case/' in question['value']

    @staticmethod
    def _save_to_case_root_path(question):
        return question['value'].split('/case/')[0]

    def _save_to_case_root_node(self, form_unique_id, question):
        """Add an extra node with the root path of the save to case to attach case properties to
        """
        question_path = self._save_to_case_root_path(question)
        response = _FormMetadataQuestion(**{
            "label": question_path,
            "tag": question_path,
            "value": question_path,
            "repeat": question['repeat'],
            "group": question['group'],
            "type": 'SaveToCase',
            "hashtagValue": question['hashtagValue'],
            "relevant": None,
            "required": False,
            "comment": None,
            "constraint": None,
            "load_properties": self._case_meta.get_load_properties(form_unique_id, question_path),
            "save_properties": self._case_meta.get_save_properties(form_unique_id, question_path)
        })
        self._seen_save_to_case[form_unique_id].append(question_path)
        return response

    def _serialized_question(self, form_unique_id, question):
        response = _FormMetadataQuestion(question)
        response.load_properties = self._case_meta.get_load_properties(form_unique_id, question['value'])
        response.save_properties = self._case_meta.get_save_properties(form_unique_id, question['value'])
        if self._is_save_to_case(question):
            response.type = 'SaveToCase'
        return response


def get_app_summary_formdata(domain, app, include_shadow_forms=True):
    """Returns formdata formatted for the app summary
    """
    return _AppSummaryFormDataGenerator(domain, app, include_shadow_forms).generate()


class AppDiffGenerator(object):
    def __init__(self, app1, app2):
        self.first = get_app_summary_formdata(app1.domain, app1)[0]
        self.second = get_app_summary_formdata(app2.domain, app2)[0]

        self._populate_id_caches()
        self._mark_removed_items()
        self._mark_added_modules()

    def _populate_id_caches(self):
        self._first_ids = set()
        self._first_forms_by_id = {}
        self._first_modules_by_id = {}
        self._first_questions_by_id = defaultdict(dict)
        self._second_ids = set()
        self._second_questions_by_id = defaultdict(dict)

        for module in self.first:
            self._first_ids.add(module['id'])
            self._first_modules_by_id[module['id']] = module
            for form in module['forms']:
                self._first_ids.add(form['id'])
                self._first_forms_by_id[form['id']] = form
                for question in form['questions']:
                    self._first_questions_by_id[form['id']][question['value']] = question

        for module in self.second:
            self._second_ids.add(module['id'])
            for form in module['forms']:
                self._second_ids.add(form['id'])
                for question in form['questions']:
                    self._second_questions_by_id[form['id']][question['value']] = question

    def _mark_removed_items(self):
        for module in self.first:
            if module.id not in self._second_ids:
                module.changes.module = REMOVED
            else:
                self._mark_removed_forms(module['forms'])

    def _mark_removed_forms(self, forms):
        for form in forms:
            if form['id'] not in self._second_ids:
                form.changes.form = REMOVED
            else:
                self._mark_removed_questions(form['id'], form.questions)

    def _mark_removed_questions(self, form_id, questions):
        for question in questions:
            if question.value not in self._second_questions_by_id[form_id]:
                question.changes.question = REMOVED

    def _mark_added_modules(self):
        for module in self.second:
            if module['id'] not in self._first_ids:
                module.changes.module = ADDED
            else:
                for attribute in MODULE_ATTRIBUTES:
                    self._mark_changed_attribute(self._first_modules_by_id[module['id']], module, attribute)
                self._mark_added_forms(module['forms'])

    def _mark_added_forms(self, forms):
        for form in forms:
            if form['id'] not in self._first_ids:
                form.changes.form = ADDED
            else:
                for attribute in FORM_ATTRIBUTES:
                    self._mark_changed_attribute(self._first_forms_by_id[form['id']], form, attribute)
                self._mark_added_questions(form['id'], form['questions'])

    def _mark_added_questions(self, form_id, questions):
        for second_question in questions:
            question_path = second_question['value']
            if question_path not in self._first_questions_by_id[form_id]:
                second_question.changes.question = ADDED
            else:
                first_question = self._first_questions_by_id[form_id][question_path]
                self._mark_changed_questions(first_question, second_question)

    def _mark_changed_questions(self, first_question, second_question):
        for attribute in QUESTION_ATTRIBUTES:
            if attribute == 'options':
                self._mark_changed_options(first_question, second_question)
            else:
                self._mark_changed_attribute(first_question, second_question, attribute)

    def _mark_changed_attribute(self, first_item, second_item, attribute):
        is_translatable_property = (isinstance(first_item[attribute], dict)
                                    and isinstance(second_item[attribute], dict))
        translation_changed = (is_translatable_property
                               and set(second_item[attribute].items()) - set(first_item[attribute].items()))
        attribute_changed = first_item[attribute] != second_item[attribute]
        attribute_added = second_item[attribute] and not first_item[attribute]
        attribute_removed = first_item[attribute] and not second_item[attribute]
        if attribute_changed or translation_changed:
            first_item.changes[attribute] = CHANGED
            second_item.changes[attribute] = CHANGED
        if attribute_added:
            second_item.changes[attribute] = ADDED
        if attribute_removed:
            first_item.changes[attribute] = REMOVED

    def _mark_changed_options(self, first_question, second_question):
        first_option_values = {option.value for option in first_question.options}
        second_option_values = {option.value for option in second_question.options}

        removed_options = first_option_values - second_option_values
        added_options = second_option_values - first_option_values

        potentially_changed_options = first_option_values & second_option_values
        first_options_by_value = {option.value: option.label for option in first_question.options}
        second_options_by_value = {option.value: option.label for option in second_question.options}
        changed_options = [
            option for option in potentially_changed_options
            if first_options_by_value[option] != second_options_by_value[option]
        ]

        for removed_option in removed_options:
            first_question.changes['options'][removed_option] = REMOVED

        for added_option in added_options:
            second_question.changes['options'][added_option] = ADDED

        for changed_option in changed_options:
            first_question.changes['options'][changed_option] = CHANGED
            second_question.changes['options'][changed_option] = CHANGED


def get_app_diff(app1, app2):
    return AppDiffGenerator(app1, app2)
