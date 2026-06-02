"""
@relation(SDOC-SRS-142, scope=file)
"""

from strictdoc.backend.sdoc_source_code.models.source_file_info import (
    SourceFileTraceabilityInfo,
)
from strictdoc.backend.sdoc_source_code.reader_rust import (
    SourceFileTraceabilityReader_Rust,
    rust_file_module_segments,
)


def _read(source: bytes, file_path: str) -> SourceFileTraceabilityInfo:
    return SourceFileTraceabilityReader_Rust().read(source, file_path=file_path)


def _function_named(info: SourceFileTraceabilityInfo, name: str):
    matches = [function for function in info.functions if function.name == name]
    assert len(matches) == 1, (
        f"expected exactly one function named {name!r}, got "
        f"{[function.name for function in info.functions]}"
    )
    return matches[0]


def test_empty_file():
    info = _read(b"", file_path="src/lib.rs")
    assert isinstance(info, SourceFileTraceabilityInfo)
    assert len(info.markers) == 0


def test_relation_marker_is_attached_to_function():
    source = b"""\
/// @relation(REQ-1, scope=function)
pub fn add(a: i32, b: i32) -> i32 {
    a + b
}
"""
    info = _read(source, file_path="src/lib.rs")
    function = _function_named(info, "lib::add")
    assert function.markers[0].reqs == ["REQ-1"]


def _read_one(source_body: bytes, file_path: str, req: str, fn_name: str):
    source = b"/// @relation(" + req.encode() + b", scope=function)\n" + source_body
    info = _read(source, file_path=file_path)
    return _function_named(info, fn_name)


def test_canonical_path_crate_root_lib():
    fn = _read_one(b"pub fn add() {}\n", "src/lib.rs", "REQ-1", "lib::add")
    assert fn.markers[0].reqs == ["REQ-1"]


def test_canonical_path_crate_root_main():
    _read_one(b"pub fn helper() {}\n", "src/main.rs", "REQ-1", "main::helper")


def test_canonical_path_top_level_module_file():
    _read_one(b"pub fn parse() {}\n", "src/model.rs", "REQ-1", "lib::model::parse")


def test_canonical_path_nested_module_file():
    _read_one(b"pub fn run() {}\n", "src/a/b/c.rs", "REQ-1", "lib::a::b::c::run")


def test_canonical_path_mod_rs_uses_directory_name():
    _read_one(b"pub fn run() {}\n", "src/model/mod.rs", "REQ-1", "lib::model::run")


def test_canonical_path_submodule_file():
    _read_one(
        b"pub fn round_trips() {}\n",
        "src/model/tests.rs",
        "REQ-9",
        "lib::model::tests::round_trips",
    )


def test_canonical_path_inline_mod_nesting():
    source = b"""\
mod tests {
    /// @relation(REQ-3, scope=function)
    pub fn it_works() {}
}
"""
    info = _read(source, file_path="src/element_id.rs")
    fn = _function_named(info, "lib::element_id::tests::it_works")
    assert fn.markers[0].reqs == ["REQ-3"]


def test_canonical_path_project_relative_path_anchors_on_src():
    _read_one(
        b"pub fn run() {}\n",
        "crates/sysml-semantic-model/src/model/tests.rs",
        "REQ-1",
        "lib::model::tests::run",
    )


def test_canonical_path_integration_test_root():
    _read_one(b"fn it_runs() {}\n", "tests/it.rs", "REQ-1", "it::it_runs")


def test_canonical_path_integration_test_submodule():
    _read_one(b"fn helps() {}\n", "tests/it/helper.rs", "REQ-1", "it::helper::helps")


def test_module_segments_mapping():
    assert rust_file_module_segments("src/lib.rs") == ["lib"]
    assert rust_file_module_segments("src/main.rs") == ["main"]
    assert rust_file_module_segments("src/model.rs") == ["lib", "model"]
    assert rust_file_module_segments("src/model/mod.rs") == ["lib", "model"]
    assert rust_file_module_segments("src/model/tests.rs") == [
        "lib",
        "model",
        "tests",
    ]
    assert rust_file_module_segments("src/a/b/c.rs") == ["lib", "a", "b", "c"]
    assert rust_file_module_segments("tests/it.rs") == ["it"]
    assert rust_file_module_segments("tests/it/helper.rs") == ["it", "helper"]
    assert rust_file_module_segments("crates/foo/src/model/tests.rs") == [
        "lib",
        "model",
        "tests",
    ]
    assert rust_file_module_segments("lib.rs") == ["lib"]
