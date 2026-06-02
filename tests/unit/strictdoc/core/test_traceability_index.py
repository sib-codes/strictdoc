"""
@relation(SDOC-SRS-28, scope=file)
"""

from strictdoc.backend.sdoc.models.node import SDocNode, SDocNodeField
from strictdoc.core.constants import (
    TEST_RESULT_NODE_TYPE,
    GraphLinkType,
    TestResultStatus,
)
from strictdoc.core.document_tree import DocumentTree
from strictdoc.core.traceability_index import TraceabilityIndex
from strictdoc.core.traceability_index_builder import TraceabilityIndexBuilder
from strictdoc.helpers.mid import MID
from tests.unit.helpers.document_builder import DocumentBuilder


def _build_index_with_one_requirement():
    document_builder = DocumentBuilder()
    requirement = document_builder.add_requirement("REQ-001")
    document = document_builder.build()
    document_tree = DocumentTree(
        file_tree=[],
        document_list=[document],
        map_docs_by_paths={},
        map_docs_by_rel_paths={},
        map_grammars_by_filenames={},
    )
    traceability_index = TraceabilityIndexBuilder.create_from_document_tree(
        document_tree, project_config=document_builder.project_config
    )
    return traceability_index, document, requirement


def _link_test_result(traceability_index, document, requirement, status):
    test_result = SDocNode(
        parent=document,
        node_type=TEST_RESULT_NODE_TYPE,
        fields=[],
        relations=[],
    )
    test_result.ordered_fields_lookup["STATUS"] = [
        SDocNodeField(
            parent=test_result,
            field_name="STATUS",
            parts=[status],
            multiline__=None,
        )
    ]
    traceability_index.graph_database.create_link(
        link_type=GraphLinkType.NODE_TO_CHILD_NODES,
        lhs_node=requirement,
        rhs_node=test_result,
        edge="IsSatisfiedBy",
    )
    return test_result


def test_test_status__no_test_results():
    traceability_index, _, requirement = _build_index_with_one_requirement()

    assert traceability_index.get_node_test_results(requirement) == []
    assert traceability_index.has_test_results(requirement) is False
    assert traceability_index.get_node_test_status(requirement) is None


def test_test_status__passed_only():
    traceability_index, document, requirement = (
        _build_index_with_one_requirement()
    )
    _link_test_result(
        traceability_index, document, requirement, TestResultStatus.PASSED
    )

    assert traceability_index.has_test_results(requirement) is True
    assert len(traceability_index.get_node_test_results(requirement)) == 1
    assert (
        traceability_index.get_node_test_status(requirement)
        == TestResultStatus.PASSED
    )


def test_test_status__failed_takes_precedence_over_passed():
    traceability_index, document, requirement = (
        _build_index_with_one_requirement()
    )
    _link_test_result(
        traceability_index, document, requirement, TestResultStatus.PASSED
    )
    _link_test_result(
        traceability_index, document, requirement, TestResultStatus.FAILED
    )

    assert (
        traceability_index.get_node_test_status(requirement)
        == TestResultStatus.FAILED
    )


def test_test_status__skipped_when_no_passed_or_failed():
    traceability_index, document, requirement = (
        _build_index_with_one_requirement()
    )
    _link_test_result(
        traceability_index, document, requirement, TestResultStatus.SKIPPED
    )

    assert (
        traceability_index.get_node_test_status(requirement)
        == TestResultStatus.SKIPPED
    )


def test_valid_01_one_document_with_1req():
    document_builder = DocumentBuilder()
    requirement = document_builder.add_requirement("REQ-001")
    document_1 = document_builder.build()

    file_tree = []
    document_list = [document_1]
    map_docs_by_paths = {}
    document_tree = DocumentTree(
        file_tree=file_tree,
        document_list=document_list,
        map_docs_by_paths=map_docs_by_paths,
        map_docs_by_rel_paths={},
        map_grammars_by_filenames={},
    )
    traceability_index = TraceabilityIndexBuilder.create_from_document_tree(
        document_tree, project_config=document_builder.project_config
    )
    parent_requirements = traceability_index.get_parent_requirements(
        requirement
    )
    assert parent_requirements == []


def test_valid_02_one_document_with_1req():
    document_builder = DocumentBuilder()
    requirement1 = document_builder.add_requirement("REQ-001")
    requirement2 = document_builder.add_requirement("REQ-002")
    requirement3 = document_builder.add_requirement("REQ-003")
    requirement4 = document_builder.add_requirement("REQ-004")
    document_builder.add_requirement_relation(
        relation_type="Parent",
        source_requirement_id="REQ-002",
        target_requirement_id="REQ-001",
        role=None,
    )
    document_builder.add_requirement_relation(
        relation_type="Parent",
        source_requirement_id="REQ-003",
        target_requirement_id="REQ-001",
        role=None,
    )
    document_builder.add_requirement_relation(
        relation_type="Parent",
        source_requirement_id="REQ-003",
        target_requirement_id="REQ-002",
        role=None,
    )
    document_builder.add_requirement_relation(
        relation_type="Parent",
        source_requirement_id="REQ-004",
        target_requirement_id="REQ-003",
        role=None,
    )

    document_1 = document_builder.build()

    file_tree = []
    document_list = [document_1]
    map_docs_by_paths = {}
    document_tree = DocumentTree(
        file_tree=file_tree,
        document_list=document_list,
        map_docs_by_paths=map_docs_by_paths,
        map_docs_by_rel_paths={},
        map_grammars_by_filenames={},
    )
    traceability_index = TraceabilityIndexBuilder.create_from_document_tree(
        document_tree, project_config=document_builder.project_config
    )
    requirement1_parents = traceability_index.get_parent_requirements(
        requirement1
    )
    assert requirement1_parents == []

    requirement2_parents = traceability_index.get_parent_requirements(
        requirement2
    )
    assert requirement2_parents == [requirement1]

    requirement3_parents = traceability_index.get_parent_requirements(
        requirement3
    )
    assert requirement3_parents == [requirement1, requirement2]

    requirement4_parents = traceability_index.get_parent_requirements(
        requirement4
    )
    assert requirement4_parents == [requirement3]


def test__adding_parent_link__01__two_requirements_in_one_document():
    document_builder = DocumentBuilder()
    requirement1 = document_builder.add_requirement("REQ-001")
    requirement2 = document_builder.add_requirement("REQ-002")
    document_1 = document_builder.build()

    file_tree = []
    document_list = [document_1]
    map_docs_by_paths = {}
    document_tree = DocumentTree(
        file_tree=file_tree,
        document_list=document_list,
        map_docs_by_paths=map_docs_by_paths,
        map_docs_by_rel_paths={},
        map_grammars_by_filenames={},
    )
    traceability_index: TraceabilityIndex = (
        TraceabilityIndexBuilder.create_from_document_tree(
            document_tree, project_config=document_builder.project_config
        )
    )
    traceability_index.update_requirement_parent_uid(
        requirement2, "REQ-001", None
    )

    # REQ2 has REQ1 as its parent.
    req2_parent_requirements = traceability_index.get_parent_requirements(
        requirement2
    )
    assert req2_parent_requirements == [requirement1]

    # REQ1 has REQ2 as its child.
    req1_child_requirements = traceability_index.get_children_requirements(
        requirement1
    )
    assert req1_child_requirements == [requirement2]


def test__adding_parent_link__02__two_requirements_in_two_documents():
    document_builder_1 = DocumentBuilder("DOC-1")
    requirement1 = document_builder_1.add_requirement("REQ-001")
    document_1 = document_builder_1.build()

    document_builder_2 = DocumentBuilder("DOC-2")
    requirement2 = document_builder_2.add_requirement("REQ-002")
    document_2 = document_builder_2.build()

    file_tree = []
    document_list = [document_1, document_2]
    map_docs_by_paths = {}
    document_tree = DocumentTree(
        file_tree=file_tree,
        document_list=document_list,
        map_docs_by_paths=map_docs_by_paths,
        map_docs_by_rel_paths={},
        map_grammars_by_filenames={},
    )
    traceability_index: TraceabilityIndex = (
        TraceabilityIndexBuilder.create_from_document_tree(
            document_tree, project_config=document_builder_1.project_config
        )
    )
    traceability_index.update_requirement_parent_uid(
        requirement2, "REQ-001", None
    )

    # REQ2 has REQ1 as its parent.
    req2_parent_requirements = traceability_index.get_parent_requirements(
        requirement2
    )
    assert req2_parent_requirements == [requirement1]

    # REQ1 has REQ2 as its child.
    req1_child_requirements = traceability_index.get_children_requirements(
        requirement1
    )
    assert req1_child_requirements == [requirement2]


def test__adding_parent_link__04__two_requirements_remove_parent_link():
    document_builder = DocumentBuilder()
    requirement1 = document_builder.add_requirement("REQ-001")
    requirement2 = document_builder.add_requirement("REQ-002")
    document_builder.add_requirement_relation(
        relation_type="Parent",
        source_requirement_id="REQ-002",
        target_requirement_id="REQ-001",
        role=None,
    )
    document_1 = document_builder.build()

    file_tree = []
    document_list = [document_1]
    map_docs_by_paths = {}
    document_tree = DocumentTree(
        file_tree=file_tree,
        document_list=document_list,
        map_docs_by_paths=map_docs_by_paths,
        map_docs_by_rel_paths={},
        map_grammars_by_filenames={},
    )
    traceability_index: TraceabilityIndex = (
        TraceabilityIndexBuilder.create_from_document_tree(
            document_tree, project_config=document_builder.project_config
        )
    )
    traceability_index.remove_requirement_parent_uid(
        requirement2, "REQ-001", role=None
    )

    req2_parent_requirements = traceability_index.get_parent_requirements(
        requirement2
    )
    assert req2_parent_requirements == []

    req1_child_requirements = traceability_index.get_children_requirements(
        requirement1
    )
    assert req1_child_requirements == []


def test_get_node_by_mid():
    document_builder = DocumentBuilder()
    document_1 = document_builder.build()

    file_tree = []
    document_list = [document_1]
    map_docs_by_paths = {}
    document_tree = DocumentTree(
        file_tree=file_tree,
        document_list=document_list,
        map_docs_by_paths=map_docs_by_paths,
        map_docs_by_rel_paths={},
        map_grammars_by_filenames={},
    )
    traceability_index: TraceabilityIndex = (
        TraceabilityIndexBuilder.create_from_document_tree(
            document_tree, project_config=document_builder.project_config
        )
    )
    assert (
        traceability_index.get_node_by_mid(MID(document_1.reserved_mid))
        == document_1
    )
