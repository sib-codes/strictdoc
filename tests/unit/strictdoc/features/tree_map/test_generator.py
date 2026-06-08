from strictdoc.backend.sdoc.models.document import SDocDocument
from strictdoc.backend.sdoc.models.node import SDocNode
from strictdoc.backend.sdoc.models.object_factory import SDocObjectFactory
from strictdoc.features.tree_map.generator import is_coverage_normative_node
from tests.unit.helpers.document_builder import DocumentBuilder


def _make_node(
    document: SDocDocument, node_type: str, *, has_requirements: bool = False
) -> SDocNode:
    node = SDocObjectFactory.create_requirement(
        parent=document, node_type=node_type
    )
    node.ng_has_requirements = has_requirements
    return node


def test_requirement_in_authored_document_is_coverage_normative():
    builder = DocumentBuilder()
    requirement = builder.add_requirement("REQ-1")
    assert is_coverage_normative_node(requirement, builder.build())


def test_section_with_requirements_is_coverage_normative():
    document = DocumentBuilder().build()
    section = _make_node(document, "SECTION", has_requirements=True)
    assert is_coverage_normative_node(section, document)


def test_empty_section_is_not_coverage_normative():
    document = DocumentBuilder().build()
    section = _make_node(document, "SECTION", has_requirements=False)
    assert not is_coverage_normative_node(section, document)


def test_text_node_is_not_coverage_normative():
    document = DocumentBuilder().build()
    assert not is_coverage_normative_node(
        _make_node(document, "TEXT"), document
    )


def test_autogen_test_report_node_is_excluded():
    # Regression: an ingested test report is an autogen document; its
    # TEST_RESULT node is is_normative_node()==True but is not a requirement and
    # must stay out of the coverage maps.
    document = DocumentBuilder().build()
    document.autogen = True
    assert not is_coverage_normative_node(
        _make_node(document, "TEST_RESULT"), document
    )
