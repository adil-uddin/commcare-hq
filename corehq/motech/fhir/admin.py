import json

from django.contrib import admin

from corehq.motech.fhir.models import FHIRResourceType, FHIRResourceProperty


def _domain(obj):
    return obj.resource_type.domain


def _case_property(obj):
    case_type = obj.resource_type.case_type.name
    if obj.case_property:
        return f'{case_type}.{obj.case_property.name}'
    if 'case_property' in obj.value_source_config:
        return f"{case_type}.{obj.value_source_config['case_property']}"
    return ''


class FHIRResourcePropertyAdmin(admin.ModelAdmin):
    model = FHIRResourceProperty
    list_display = (
        _domain,
        'resource_type',
        'value_source_jsonpath',
        _case_property
    )
    list_display_links = (
        _domain,
        'resource_type',
        'value_source_jsonpath',
    )
    list_filter = ('resource_type__domain',)
    list_select_related = ('resource_type', 'resource_type__case_type')

    readonly_fields = ('resource_type', 'case_property')

    def has_add_permission(self, request):
        # Domains are difficult to manage with this interface. Create
        # using the Data Dictionary, and edit in Admin.
        return False


class FHIRResourcePropertyInline(admin.TabularInline):
    model = FHIRResourceProperty
    verbose_name_plural = 'FHIR resource properties'
    fields = ('calculated_value_source', 'value_source_config',)
    readonly_fields = ('calculated_value_source',)

    def calculated_value_source(self, obj):
        if not (obj.case_property and obj.jsonpath):
            return ''

        value_source_config = {
            'case_property': obj.case_property.name,
            'jsonpath': obj.jsonpath,
        }
        if obj.value_map:
            value_source_config['value_map'] = obj.value_map

        return json.dumps(value_source_config, indent=2)


class FHIRResourceTypeAdmin(admin.ModelAdmin):
    model = FHIRResourceType
    list_display = (
        'domain',
        'name',
        'case_type',
    )
    list_display_links = (
        'domain',
        'name',
        'case_type',
    )
    list_filter = ('domain',)

    # Allows for creating resource properties without having to deal
    # with domains.
    inlines = [FHIRResourcePropertyInline]

    def has_add_permission(self, request):
        # Domains are difficult to manage with this interface. Create
        # using the Data Dictionary, and edit in Admin.
        return False


admin.site.register(FHIRResourceType, FHIRResourceTypeAdmin)
admin.site.register(FHIRResourceProperty, FHIRResourcePropertyAdmin)
