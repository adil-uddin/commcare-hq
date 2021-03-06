import datetime
import uuid

from django.http import QueryDict
from django.test import TestCase

from casexml.apps.case.mock import CaseBlock, IndexAttrs
from pillowtop.es_utils import initialize_index_and_mapping

from corehq import privileges
from corehq.apps.es.tests.utils import es_test
from corehq.elastic import get_es_new, send_to_elasticsearch
from corehq.form_processor.tests.utils import FormProcessorTestUtils
from corehq.pillows.case_search import transform_case_for_elasticsearch
from corehq.pillows.mappings.case_search_mapping import CASE_SEARCH_INDEX_INFO
from corehq.util.elastic import ensure_index_deleted
from corehq.util.test_utils import (
    generate_cases,
    privilege_enabled,
    trap_extra_setup,
)

from ..api.core import UserError
from ..api.get_list import get_list, MAX_PAGE_SIZE
from ..utils import submit_case_blocks


@es_test
@privilege_enabled(privileges.API_ACCESS)
class TestCaseListAPI(TestCase):
    domain = 'testcaselistapi'

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.cases = cls._mk_cases()
        cls.es = get_es_new()
        with trap_extra_setup(ConnectionError):
            initialize_index_and_mapping(cls.es, CASE_SEARCH_INDEX_INFO)
        for case in cls.cases:
            send_to_elasticsearch(
                'case_search',
                transform_case_for_elasticsearch(case.to_json())
            )
        cls.es.indices.refresh(CASE_SEARCH_INDEX_INFO.index)

    @classmethod
    def _mk_cases(cls):
        case_blocks = []
        good_id = str(uuid.uuid4())
        bad_id = str(uuid.uuid4())
        for team_id, name in [(good_id, 'good_guys'), (bad_id, 'bad_guys')]:
            case_blocks.append(CaseBlock(
                case_id=team_id,
                case_type='team',
                case_name=name,
                external_id=name,
                owner_id='team_owner',
                create=True,
            ))

        date_opened = datetime.datetime(1878, 2, 17, 12)
        for external_id, name, properties, team_id in [
                ('mattie', "Mattie Ross", {}, good_id),
                ('rooster', "Reuben Cogburn", {"alias": "Rooster"}, good_id),
                ('laboeuf', "LaBoeuf", {"alias": ""}, good_id),
                ('chaney', "Tom Chaney", {"alias": "The Coward"}, bad_id),
                ('ned', "Ned Pepper", {"alias": "Lucky Ned"}, bad_id),
        ]:
            case_blocks.append(CaseBlock(
                case_id=str(uuid.uuid4()),
                case_type='person',
                case_name=name,
                external_id=external_id,
                owner_id='person_owner',
                date_opened=date_opened,
                create=True,
                update=properties,
                index={'parent': IndexAttrs('team', team_id, 'child')}
            ))
            date_opened += datetime.timedelta(days=1)

        case_blocks[-1].close = True  # close Ned Pepper

        _, cases = submit_case_blocks([cb.as_text() for cb in case_blocks], domain=cls.domain)

        # preserve ordering so inserted_at date lines up right in ES
        order = {cb.external_id: index for index, cb in enumerate(case_blocks)}
        return sorted(cases, key=lambda case: order[case.external_id])

    @classmethod
    def tearDownClass(cls):
        FormProcessorTestUtils.delete_all_cases()
        ensure_index_deleted(CASE_SEARCH_INDEX_INFO.index)
        super().tearDownClass()


@generate_cases([
    ("", ['good_guys', 'bad_guys', 'mattie', 'rooster', 'laboeuf', 'chaney', 'ned']),
    ("limit=2", ['good_guys', 'bad_guys']),
    ("external_id=mattie", ['mattie']),
    ("external_id=the-man-with-no-name", []),
    ("case_type=team", ["good_guys", "bad_guys"]),
    ("owner_id=person_owner", ['mattie', 'rooster', 'laboeuf', 'chaney', 'ned']),
    ("case_name=Mattie Ross", ["mattie"]),
    ("case_name=Mattie+Ross", ["mattie"]),
    ("case_name=Mattie", []),
    ("closed=true", ["ned"]),
    ("date_opened.lt=1878-02-19", ["mattie", "rooster"]),
    ("date_opened.lte=1878-02-19", ["mattie", "rooster", "laboeuf"]),
    ("date_opened.lte=1878-02-19T00:00:00", ["mattie", "rooster"]),
    ("date_opened.gt=1878-02-18&date_opened.lt=1878-02-20", ["laboeuf"]),
    ("date_opened.gt=1878-02-19T11:00:00&date_opened.lt=1878-02-19T13:00:00", ["laboeuf"]),
    ("date_opened.lt=1878-02-18&date_opened.gt=1878-02-19", []),
    ("property.alias=Rooster", ["rooster"]),
    ("property.alias=rooster", []),
    ('property.foo {"test": "json"}=bar', []),  # This is escaped as expected
    ('property.foo={"test": "json"}', []),  # This is escaped as expected
    ("case_type=person&property.alias=", ["mattie", "laboeuf"]),
    ('xpath=(alias="Rooster" or name="Mattie Ross")', ["mattie", "rooster"]),
], TestCaseListAPI)
def test_case_list_queries(self, querystring, expected):
    params = QueryDict(querystring).dict()
    actual = [c['external_id'] for c in get_list(self.domain, params)]
    # order matters, so this doesn't use assertItemsEqual
    self.assertEqual(actual, expected)


@generate_cases([
    ("limit=nolimitz", "'nolimitz' is not a valid value for 'limit'"),
    (f"limit={MAX_PAGE_SIZE + 2}", f"You cannot request more than {MAX_PAGE_SIZE} cases per request."),
    ("date_opened.lt=bad-datetime", "Cannot parse datetime 'bad-datetime'"),
    ("date_opened.lt=2020-02-30", "Cannot parse datetime '2020-02-30'"),
    ("password=1234", "'password' is not a valid parameter."),
    ("case_name.gte=a", "'case_name.gte' is not a valid parameter."),
    ("date_opened=2020-01-30", "'date_opened' is not a valid parameter."),
    ('xpath=gibberish',
     "Bad XPath: Your search query is required to have at least one boolean "
     "operator (>, >=, <, <=, =, !=)"),
], TestCaseListAPI)
def test_bad_requests(self, querystring, error_msg):
    with self.assertRaises(UserError) as e:
        params = QueryDict(querystring).dict()
        get_list(self.domain, params)
    self.assertEqual(str(e.exception), error_msg)
