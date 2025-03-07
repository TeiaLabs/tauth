"""Generate API reference pages and navigation."""

from pathlib import Path

import mkdocs_gen_files


def build_reference_docs(library_path: Path):
    """
    Builds the reference documentation for the library.

    Automatically generates the reference documentation for Python modules
    and packages and creates a navigation file.

    Args:
        library_path: path to the library's root directory.
    """
    nav = mkdocs_gen_files.Nav()

    for path in sorted(library_path.rglob("*.py")):
        module_path = path.relative_to(library_path.parent).with_suffix("")
        doc_path = path.relative_to(library_path.parent).with_suffix(".md")
        full_doc_path = Path("reference", doc_path)

        parts = tuple(module_path.parts)

        if parts[-1] == "__init__":
            parts = parts[:-1]
            doc_path = doc_path.with_name("index.md")
            full_doc_path = full_doc_path.with_name("index.md")
        elif parts[-1] == "__main__":
            continue

        nav[parts] = doc_path.as_posix()

        with mkdocs_gen_files.open(full_doc_path, "w") as fd:
            ident = ".".join(parts)
            fd.write(f"::: {ident}")

        mkdocs_gen_files.set_edit_path(full_doc_path, path)

    with mkdocs_gen_files.open("reference/SUMMARY.md", "w") as nav_file:
        nav_file.writelines(nav.build_literate_nav())


# Change this to point to the package's root directory
library_path = Path(__file__).parents[2] / "tauth"
build_reference_docs(library_path=library_path)
