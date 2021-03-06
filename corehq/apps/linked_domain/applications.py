from collections import defaultdict

from django.conf import settings

from corehq.apps.app_manager.dbaccessors import (
    get_brief_apps_in_domain,
    get_brief_app_docs_in_domain,
    get_build_doc_by_version,
    get_latest_released_app,
    get_latest_released_app_versions_by_app_id,
    wrap_app,
)
from corehq.apps.app_manager.exceptions import AppLinkError
from corehq.apps.linked_domain.models import DomainLink
from corehq.apps.linked_domain.exceptions import MultipleDownstreamAppsError, RemoteRequestError
from corehq.apps.linked_domain.remote_accessors import (
    get_app_by_version,
    get_brief_apps,
    get_latest_released_versions_by_app_id,
    get_released_app,
)
from corehq.apps.linked_domain.util import pull_missing_multimedia_for_app
from corehq.util.quickcache import quickcache


def get_master_app_briefs(domain_link, family_id):
    if domain_link.is_remote:
        apps = get_brief_apps(domain_link)
    else:
        apps = get_brief_apps_in_domain(domain_link.master_domain, include_remote=False)

    # Ignore deleted, linked and remote apps
    return [app for app in apps if family_id in [app._id, app.family_id] and app.doc_type == 'Application']


def get_master_app_by_version(domain_link, upstream_app_id, upstream_version):
    if domain_link.is_remote:
        app = get_app_by_version(domain_link, upstream_app_id, upstream_version)
    else:
        app = get_build_doc_by_version(domain_link.master_domain, upstream_app_id, upstream_version)

    if app:
        return wrap_app(app)


def get_downstream_app_id(downstream_domain, upstream_app_id):
    downstream_ids = _get_downstream_app_id_map(downstream_domain)[upstream_app_id]
    if not downstream_ids:
        return None
    if len(downstream_ids) > 1:
        raise MultipleDownstreamAppsError
    return downstream_ids[0]


def get_upstream_app_ids(downstream_domain):
    return list(_get_downstream_app_id_map(downstream_domain))


@quickcache(vary_on=['downstream_domain'], skip_arg=lambda _: settings.UNIT_TESTING, timeout=5 * 60)
def _get_downstream_app_id_map(downstream_domain):
    downstream_app_ids = defaultdict(list)
    for doc in get_brief_app_docs_in_domain(downstream_domain):
        if doc.get("family_id"):
            downstream_app_ids[doc["family_id"]].append(doc["_id"])
    return downstream_app_ids


def get_latest_master_app_release(domain_link, app_id):
    master_domain = domain_link.master_domain
    linked_domain = domain_link.linked_domain
    if domain_link.is_remote:
        return get_released_app(master_domain, app_id, linked_domain, domain_link.remote_details)
    else:
        return get_latest_released_app(master_domain, app_id)


def get_latest_master_releases_versions(domain_link):
    if domain_link.is_remote:
        return get_latest_released_versions_by_app_id(domain_link)
    else:
        return get_latest_released_app_versions_by_app_id(domain_link.master_domain)


def create_linked_app(master_domain, master_id, target_domain, target_name, remote_details=None):
    from corehq.apps.app_manager.models import LinkedApplication
    linked_app = LinkedApplication(
        name=target_name,
        domain=target_domain,
    )
    return link_app(linked_app, master_domain, master_id, remote_details)


def link_app(linked_app, master_domain, master_id, remote_details=None):
    DomainLink.link_domains(linked_app.domain, master_domain, remote_details)

    linked_app.family_id = master_id
    linked_app.doc_type = 'LinkedApplication'
    linked_app.save()

    if linked_app.master_is_remote:
        try:
            pull_missing_multimedia_for_app(linked_app)
        except RemoteRequestError:
            raise AppLinkError('Error fetching multimedia from remote server. Please try again later.')

    _get_downstream_app_id_map.clear(linked_app.domain)
    return linked_app
