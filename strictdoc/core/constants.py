from enum import IntEnum


class GraphLinkType(IntEnum):
    MID_TO_NODE = 1
    UID_TO_NODE = 2
    NODE_TO_PARENT_NODES = 3
    NODE_TO_CHILD_NODES = 4
    NODE_TO_INCOMING_LINKS = 5
    DOCUMENT_TO_TAGS = 8


# node_type of the SDoc nodes generated for each test case when a JUnit XML
# test report is ingested (see JUnitXMLReader). Shared so that the reader that
# produces these nodes and the traceability queries that consume them agree.
TEST_RESULT_NODE_TYPE = "TEST_RESULT"


class TestResultStatus:
    PASSED = "PASSED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"
