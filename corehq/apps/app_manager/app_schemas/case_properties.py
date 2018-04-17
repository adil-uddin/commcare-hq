from __future__ import absolute_import
from __future__ import unicode_literals
from collections import defaultdict
import functools
from itertools import chain, groupby
from operator import attrgetter
import logging

from corehq import toggles
from corehq.apps.app_manager.const import USERCASE_TYPE
from corehq.apps.app_manager.dbaccessors import get_case_sharing_apps_in_domain
from corehq.apps.app_manager.util import is_usercase_in_use, all_apps_by_domain
from corehq.apps.data_dictionary.models import CaseProperty
from corehq.util.quickcache import quickcache
from memoized import memoized
import six


logger = logging.getLogger(__name__)


def _get_forms(app):
    """
    Return list of forms in the app
    """
    if app.doc_type == 'RemoteApp':
        return []
    forms = []
    for module in app.get_modules():
        forms.extend(module.get_forms())
    return forms


def _zip_update(properties_by_case_type, additional_properties_by_case_type):
    for case_type, case_properties in additional_properties_by_case_type.items():
        properties_by_case_type[case_type].update(case_properties)


class ParentCasePropertyBuilder(object):

    def __init__(self, app, defaults=(), per_type_defaults=None):
        self.app = app
        self.defaults = defaults
        self.per_type_defaults = per_type_defaults or {}

    def _get_relevant_apps(self, include_shared_properties):
        apps = [self.app]
        if self.app.case_sharing and include_shared_properties:
            apps.extend(self._get_other_case_sharing_apps_in_domain())
        return apps

    @memoized
    def _get_relevant_forms(self, include_shared_properties):
        forms = []
        for app in self._get_relevant_apps(include_shared_properties):
            forms.extend(_get_forms(app))
        return forms

    @memoized
    def _get_all_case_updates(self, include_shared_properties):
        all_case_updates = defaultdict(set)
        for form in self._get_relevant_forms(include_shared_properties):
            for case_type, case_properties in form.get_all_case_updates().items():
                all_case_updates[case_type].update(case_properties)
        return all_case_updates

    @memoized
    def _get_data_dictionary_properties_by_case_type(self):
        return {
            case_type: {prop.name for prop in props} for case_type, props in groupby(
                CaseProperty.objects
                .filter(case_type__domain=self.app.domain, deprecated=False)
                .order_by('case_type__name'),
                key=attrgetter('case_type.name')
            ).items()
        }

    def get_case_relationships_for_case_type(self, case_type, include_shared_properties=True):
        return self.get_case_relationships(include_shared_properties)[case_type]

    @memoized
    def get_case_relationships(self, include_shared_properties=True):
        case_relationships_by_child_type = defaultdict(set)

        for form in self._get_relevant_forms(include_shared_properties):
            for case_type, case_relationships in form.get_contributed_case_relationships().items():
                case_relationships_by_child_type[case_type].update(case_relationships)
        return case_relationships_by_child_type

    def get_parent_types(self, case_type):
        parent_types = self.get_case_relationships_for_case_type(case_type)
        return set(p[0] for p in parent_types)

    @memoized
    def _get_other_case_sharing_apps_in_domain(self):
        return get_case_sharing_apps_in_domain(self.app.domain, self.app.id)

    @memoized
    def get_properties(self, case_type, already_visited=(),
                       include_shared_properties=True,
                       include_parent_properties=True):
        # TODO add parent property updates to the parent case type(s) of m_case_type
        # Currently if a property is only ever updated via parent property
        # reference, then I think it will not appear in the schema.

        if case_type in already_visited:
            return ()

        case_properties_by_case_type = defaultdict(set)

        _zip_update(case_properties_by_case_type,
                    self._get_all_case_updates(include_shared_properties))

        _zip_update(case_properties_by_case_type, self.per_type_defaults)

        if toggles.DATA_DICTIONARY.enabled(self.app.domain):
            _zip_update(case_properties_by_case_type, self._get_data_dictionary_properties_by_case_type())

        case_relationships = self.get_case_relationships_for_case_type(
            case_type, include_shared_properties)

        for case_properties_ in case_properties_by_case_type.values():
            case_properties_.update(self.defaults)

        case_properties = case_properties_by_case_type[case_type]

        if include_parent_properties:
            get_properties_recursive = functools.partial(
                self.get_properties,
                already_visited=already_visited + (case_type,),
                include_shared_properties=include_shared_properties
            )
            for case_type, identifier in case_relationships:
                for property in get_properties_recursive(case_type):
                    case_properties.add('%s/%s' % (identifier, property))
        else:
            # exclude case updates that reference properties like "parent/property_name"
            case_properties = {p for p in case_properties if "/" not in p}

        return case_properties

    def get_parent_type_map(self, case_types, allow_multiple_parents=False):
        """
        :returns: A dict
        ```
        {<case_type>: {<relationship>: <parent_type>, ...}, ...}
        ```
        """
        parent_map = defaultdict(dict)

        for case_type, case_relationships in self.get_case_relationships().items():
            rel_map = defaultdict(list)
            for parent_type, relationship in case_relationships:
                rel_map[relationship].append(parent_type)

            for relationship, types in rel_map.items():
                if allow_multiple_parents:
                    parent_map[case_type][relationship] = types
                else:
                    if len(types) > 1:
                        logger.error(
                            "Case Type '%s' in app '%s' has multiple parents for relationship '%s': %s",
                            case_type, self.app.id, relationship, types
                        )
                    parent_map[case_type][relationship] = types[0]

        if case_types is not None:
            return {case_type: rel_map for case_type, rel_map in parent_map.items()
                    if case_type in case_types}
        return parent_map

    def get_case_property_map(self, case_types,
                              include_shared_properties=True,
                              include_parent_properties=True):
        case_types = sorted(case_types)
        return {
            case_type: sorted(self.get_properties(
                case_type,
                include_shared_properties=include_shared_properties,
                include_parent_properties=include_parent_properties,
            ))
            for case_type in case_types
        }


def get_case_relationships(app):
    builder = ParentCasePropertyBuilder(app)
    return builder.get_parent_type_map(app.get_case_types())


def get_case_properties(app, case_types, defaults=(),
                        include_shared_properties=True,
                        include_parent_properties=True):
    per_type_defaults = get_per_type_defaults(app.domain, case_types)
    builder = ParentCasePropertyBuilder(app, defaults, per_type_defaults=per_type_defaults)
    return builder.get_case_property_map(
        case_types,
        include_shared_properties=include_shared_properties,
        include_parent_properties=include_parent_properties,
    )


def get_all_case_properties(app):
    return get_case_properties(app, app.get_case_types(), defaults=('name',))


def get_all_case_properties_for_case_type(domain, case_type):
    return all_case_properties_by_domain(domain, [case_type]).get(case_type, [])


def get_usercase_properties(app):
    if is_usercase_in_use(app.domain):
        # TODO: add name here once it is fixed to concatenate first and last in form builder
        default_properties = {'first_name', 'last_name', 'phone_number', 'username'}
        case_properties = get_case_properties(app, [USERCASE_TYPE])
        case_properties[USERCASE_TYPE] = list(set(case_properties[USERCASE_TYPE]) | default_properties)
        return case_properties
    return {USERCASE_TYPE: []}


def all_case_properties_by_domain(domain, case_types=None, include_parent_properties=True):
    result = {}
    for app in all_apps_by_domain(domain):
        if app.is_remote_app():
            continue

        if case_types is None:
            case_types = app.get_case_types()

        property_map = get_case_properties(app, case_types,
            defaults=('name',), include_parent_properties=include_parent_properties)

        for case_type, properties in six.iteritems(property_map):
            if case_type in result:
                result[case_type].extend(properties)
            else:
                result[case_type] = properties

    cleaned_result = {}
    for case_type, properties in six.iteritems(result):
        properties = list(set(properties))
        properties.sort()
        cleaned_result[case_type] = properties

    return cleaned_result


def get_per_type_defaults(domain, case_types=None):
    from corehq.apps.callcenter.utils import get_call_center_case_type_if_enabled

    per_type_defaults = {}
    if (not case_types and is_usercase_in_use(domain)) or USERCASE_TYPE in case_types:
        per_type_defaults = {
            USERCASE_TYPE: get_usercase_default_properties(domain)
        }

    callcenter_case_type = get_call_center_case_type_if_enabled(domain)
    if callcenter_case_type and (not case_types or callcenter_case_type in case_types):
        per_type_defaults[callcenter_case_type] = get_usercase_default_properties(domain)

    return per_type_defaults


def get_shared_case_types(app):
    shared_case_types = set()

    if app.case_sharing:
        apps = get_case_sharing_apps_in_domain(app.domain, app.id)
        for app in apps:
            shared_case_types |= set(chain(*[m.get_case_types() for m in app.get_modules()]))

    return shared_case_types


@quickcache(['domain'])
def get_usercase_default_properties(domain):
    from corehq.apps.custom_data_fields.models import CustomDataFieldsDefinition
    from corehq.apps.users.views.mobile.custom_data_fields import CUSTOM_USER_DATA_FIELD_TYPE

    fields_def = CustomDataFieldsDefinition.get_or_create(domain, CUSTOM_USER_DATA_FIELD_TYPE)
    return [f.slug for f in fields_def.fields]
