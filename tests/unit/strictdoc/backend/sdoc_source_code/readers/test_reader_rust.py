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
