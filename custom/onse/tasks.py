import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date
from time import sleep
from typing import Iterable, List, Optional, Union

import attr
from celery.schedules import crontab
from celery.task import periodic_task
from requests import RequestException

from casexml.apps.case.mock import CaseBlock
from casexml.apps.case.models import CommCareCase
from dimagi.utils.chunked import chunked

from corehq.apps.hqcase.utils import submit_case_blocks
from corehq.form_processor.interfaces.dbaccessors import CaseAccessors
from corehq.form_processor.models import CommCareCaseSQL
from corehq.motech.models import ConnectionSettings
from corehq.util.soft_assert import soft_assert
from custom.onse.const import CASE_TYPE, CONNECTION_SETTINGS_NAME, DOMAIN
from custom.onse.models import iter_mappings

# The production DHIS2 server is on the other side of an
# interoperability service that changes the URL schema from
# "base_url/api/resource" to "service/dhis2core/api/v0/resource".
# Its ConnectionSettings instance uses URL "service/dhis2core/api/v0/"
# Set ``DROP_API_PREFIX = True`` to drop the "/api" before "/resource",
# so that resource URLs end up as "service/dhis2core/api/v0/resource".
DROP_API_PREFIX = True

MAX_THREAD_WORKERS = 10

_soft_assert = soft_assert('@'.join(('nhooper', 'dimagi.com')))


@attr.s(auto_attribs=True)
class CassiusMarcellus:  # TODO: Come up with a better name. Please!
    """
    Stores a case, and its updates.

    Allows us to read current case property values and build a CaseBlock
    """
    case: Union[CommCareCase, CommCareCaseSQL]
    updates: dict = attr.Factory(dict)

    @property
    def case_block(self):
        return CaseBlock(
            case_id=self.case.case_id,
            external_id=self.case.external_id,
            case_type=CASE_TYPE,
            case_name=self.case.name,
            update=self.updates,
        )


@periodic_task(
    # Run on the 5th day of every quarter
    run_every=crontab(day_of_month=5, month_of_year='1,4,7,10',
                      hour=22, minute=30),
    queue='background_queue',
)
def update_facility_cases_from_dhis2_data_elements(
    period: Optional[str] = None,
    print_notifications: bool = False,
):
    """
    Update facility_supervision cases with indicators collected in DHIS2
    over the last quarter.

    :param period: The period of data to import. e.g. "2020Q1". Defaults
        to last quarter.
    :param print_notifications: If True, notifications are printed,
        otherwise they are emailed.

    """
    dhis2_server = get_dhis2_server(print_notifications)
    if not period:
        period = get_last_quarter()
    try:
        clays = get_clays()
        with ThreadPoolExecutor(max_workers=MAX_THREAD_WORKERS) as executor:
            futures = (executor.submit(set_case_updates,
                                       dhis2_server, clay, period)
                       for clay in clays)
            for futures_chunk in chunked(futures, 100):
                case_blocks_chunk = []
                for future in as_completed(futures_chunk):
                    case_block = future.result()  # reraises exceptions in workers
                    case_blocks_chunk.append(case_block)
                save_cases(case_blocks_chunk)
    except Exception as err:
        handle_error(err, dhis2_server, print_notifications)
    else:
        handle_success(dhis2_server, print_notifications)


def get_dhis2_server(
    print_notifications: bool = False
) -> ConnectionSettings:
    try:
        return ConnectionSettings.objects.get(domain=DOMAIN,
                                              name=CONNECTION_SETTINGS_NAME)
    except ConnectionSettings.DoesNotExist:
        message = (f'ConnectionSettings {CONNECTION_SETTINGS_NAME!r} not '
                   f'found in domain {DOMAIN!r} for importing DHIS2 data '
                   f'elements.')
        if print_notifications:
            print(message, file=sys.stderr)
        else:
            _soft_assert(False, message)
        raise


def get_clays() -> Iterable[CassiusMarcellus]:
    case_accessors = CaseAccessors(DOMAIN)
    for case_id in case_accessors.get_case_ids_in_domain(type=CASE_TYPE):
        case = case_accessors.get_case(case_id)
        if not case.external_id:
            # This case is not mapped to a facility in DHIS2.
            continue
        yield CassiusMarcellus(case)


def set_case_updates(
    dhis2_server: ConnectionSettings,
    clay: CassiusMarcellus,
    period: str,
) -> CassiusMarcellus:
    """
    Fetch data sets of data elements for last quarter from ``dhis2_server``
    and update the data elements corresponding case properties in
    ``case_block`` in place.
    """
    # Several of the data elements we want belong to the same data
    # sets. Only fetch a data set if we don't already have it.
    data_set_cache = {}
    for mapping in iter_mappings():
        if not mapping.data_set_id:
            raise ValueError(
                f'Mapping {mapping} does not include data set ID. '
                'Use **fetch_onse_data_set_ids** command.')
        if mapping.data_set_id not in data_set_cache:
            data_set_cache[mapping.data_set_id] = fetch_data_set(
                dhis2_server, mapping.data_set_id,
                # facility case external_id is set to its DHIS2 org
                # unit. This is the DHIS2 facility whose data we
                # want to import.
                org_unit_id=clay.case.external_id,
                period=period,
            )
        if data_set_cache[mapping.data_set_id] is None:
            # No data for this facility. `None` = "We don't know"
            clay.updates[mapping.case_property] = None
        else:
            clay.updates[mapping.case_property] = get_data_element_total(
                mapping.data_element_id,
                data_values=data_set_cache[mapping.data_set_id]
            )
    return clay


def fetch_data_set(
    dhis2_server: ConnectionSettings,
    data_set_id: str,
    org_unit_id: str,
    period: str,
) -> Optional[List[dict]]:
    """
    Returns a list of `DHIS2 data values`_, or ``None`` if the the given
    org unit has no data collected for the last quarter.

    Raises exceptions on connection timeout or non-200 response status.


    .. _DHIS2 data values: https://docs.dhis2.org/master/en/developer/html/webapi_data_values.html

    """
    max_attempts = 3
    backoff_seconds = 5

    def is_500_error(err):
        return (
            err.response is not None
            and 500 <= err.response.status_code < 600
        )

    requests = dhis2_server.get_requests()
    endpoint = '/dataValueSets' if DROP_API_PREFIX else '/api/dataValueSets'
    params = {
        'period': period,
        'dataSet': data_set_id,
        'orgUnit': org_unit_id,
    }
    attempt = 0
    while True:
        attempt += 1
        try:
            response = requests.get(endpoint, params, raise_for_status=True)
        except RequestException as err:
            if is_500_error(err) and attempt < max_attempts:
                sleep(backoff_seconds * attempt)
            else:
                raise
        else:
            break
    return response.json().get('dataValues', None)


def get_last_quarter(today: Optional[date] = None) -> str:
    """
    Returns the last quarter in  DHIS2 web API `period format`_.
    e.g. "2004Q1"

    .. _period format: https://docs.dhis2.org/master/en/developer/html/webapi_date_perid_format.html
    """
    if today is None:
        today = date.today()
    year = today.year
    last_quarter = (today.month - 1) // 3
    if last_quarter == 0:
        year -= 1
        last_quarter = 4
    return f"{year}Q{last_quarter}"


def get_data_element_total(
    data_element_id: str,
    data_values: List[dict],
) -> int:
    """
    A DHIS2 data element may be broken down by category options, and
    ``data_values`` can contain multiple entries for the same data
    element. This function returns the total for a given
    ``data_element_id``.

    The following doctest shows an example value for ``data_values`` as
    might be returned by DHIS2:

    >>> data_values = [
    ...     {
    ...         "dataElement": "f7n9E0hX8qk",
    ...         "period": "2014Q1",
    ...         "orgUnit": "DiszpKrYNg8",
    ...         "categoryOption": "FNnj3jKGS7i",
    ...         "value": "12"
    ...     },
    ...     {
    ...         "dataElement": "f7n9E0hX8qk",
    ...         "period": "2014Q1",
    ...         "orgUnit": "DiszpKrYNg8",
    ...         "categoryOption": "Jkhdsf8sdf4",
    ...         "value": "16"
    ...     }
    ... ]
    >>> get_data_element_total('f7n9E0hX8qk', data_values)
    28

    """
    value = 0
    for data_value in data_values:
        if data_value['dataElement'] == data_element_id:
            value += int(data_value['value'])
    return value


def save_cases(clays: List[CassiusMarcellus]):
    today = date.today().isoformat()
    submit_case_blocks(
        [clay.case_block.as_text() for clay in clays],
        DOMAIN,
        xmlns='http://commcarehq.org/dhis2-import',
        device_id=f"dhis2-import-{DOMAIN}-{today}",
    )


def handle_error(
    err: Exception,
    dhis2_server: ConnectionSettings,
    print_notifications: bool,
):
    message = f'Importing ONSE ISS facility cases from DHIS2 failed: {err}'
    if print_notifications:
        print(message, file=sys.stderr)
    else:
        dhis2_server.get_requests().notify_exception(message)
        raise err


def handle_success(
    dhis2_server: ConnectionSettings,
    print_notifications: bool,
):
    message = 'Successfully imported ONSE ISS facility cases from DHIS2'
    if print_notifications:
        print(message, file=sys.stderr)
    else:
        # For most things we pass silently. But we can repurpose
        # `notify_error()` to tell admins that the import went through,
        # because it only happens once a quarter.
        dhis2_server.get_requests().notify_error(message)
