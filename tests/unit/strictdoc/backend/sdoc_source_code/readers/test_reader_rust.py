"""
@relation(SDOC-SRS-142, scope=file)
"""

from strictdoc.backend.sdoc_source_code.models.source_file_info import (
    SourceFileTraceabilityInfo,
)
from strictdoc.backend.sdoc_source_code.reader_rust import (
    SourceFileTraceabilityReader_Rust,
)


def test_00_empty_file():
    input_string = b""""""

    reader = SourceFileTraceabilityReader_Rust()

    info = reader.read(input_string)

    assert isinstance(info, SourceFileTraceabilityInfo)
    assert len(info.markers) == 0


def test_function_relation_marker_is_attached_to_function():
    # Regression test: the Rust reader collected a function's requirement
    # markers but then constructed the function with markers=[], dropping them.
    # The C/C++ reader attaches them, and FileTraceabilityIndex relies on
    # function.markers to connect test results back to the requirements they
    # verify. The marker must therefore live on the function, not only in the
    # file-level marker list.
    input_string = b"""\
/// @relation(REQ-1, scope=function)
pub fn add(a: i32, b: i32) -> i32 {
    a + b
}
"""

    reader = SourceFileTraceabilityReader_Rust()
    info: SourceFileTraceabilityInfo = reader.read(
        input_string, file_path="lib.rs"
    )

    assert isinstance(info, SourceFileTraceabilityInfo)

    functions_with_markers = [
        function_ for function_ in info.functions if len(function_.markers) > 0
    ]
    assert len(functions_with_markers) == 1, (
        "Expected the requirement marker to be attached to the function. "
        f"Functions: {[(f.name, f.markers) for f in info.functions]}"
    )

    function = functions_with_markers[0]
    assert function.name == "lib::add"
    assert function.markers[0].reqs == ["REQ-1"]


def test_function_range_folds_in_leading_attributes_and_doc_comment():
    # Regression test: tree-sitter models a function's doc comment and outer
    # attributes (e.g. #[test]) as siblings of the function_item node, so the
    # node alone starts at the `fn` keyword. The function range must extend up
    # to the doc comment so a linked test result renders the whole function -
    # including its #[test] and documentation - and not just the bare body.
    # Mirrors the C/C++ reader's "function range includes the top comment".
    input_string = b"""\
#[cfg(test)]
mod tests {
    /// @relation(REQ-1, scope=function)
    #[test]
    fn add_works() {
        assert_eq!(2 + 2, 4);
    }
}
"""

    reader = SourceFileTraceabilityReader_Rust()
    info: SourceFileTraceabilityInfo = reader.read(
        input_string, file_path="lib.rs"
    )

    function = next(
        function_
        for function_ in info.functions
        if function_.name == "lib::tests::add_works"
    )

    # Lines: 3 = doc comment, 4 = #[test], 5 = fn, 7 = closing brace.
    assert function.line_begin == 3
    assert function.line_end == 7

    # The enclosing module folds in its own #[cfg(test)] attribute (line 1).
    module = next(
        function_
        for function_ in info.functions
        if function_.name == "lib::tests"
    )
    assert module.line_begin == 1
