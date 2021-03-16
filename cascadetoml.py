# SPDX-FileCopyrightText: Copyright (c) 2021 Scott Shawcroft for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""Command for cascading toml files together"""

import csv
import pathlib
import sys
import typing
import typer
import tomlkit
import parse

import tabulate as tabulate_lib

# grumble grumble. This is the VCS' job.
__version__ = "0.2.0"

app = typer.Typer()

refactor_app = typer.Typer()
app.add_typer(refactor_app, name="refactor")

cascade_app = typer.Typer()
app.add_typer(cascade_app, name="cascade")


def _cascade(paths: typing.List[pathlib.Path]) -> tomlkit.document:
    # pylint: disable=too-many-locals,too-many-branches,too-many-statements
    output_doc = tomlkit.document()

    root_cache = {}
    for path in paths:
        full_path = path.resolve()
        # Find the cascade root
        root = None
        for parent in full_path.parents:
            possible_root = parent / ".cascade.toml"
            if possible_root.is_file():
                root = possible_root
                break
        if not root:
            print("No root found for", path)
            continue

        if root not in root_cache:
            loaded_info = tomlkit.parse(root.read_text())
            root_cache[root] = loaded_info
            implied_paths = []
            for path_template in loaded_info["paths"]:
                path_template = pathlib.Path(path_template)
                for parent in path_template.parents:
                    if not parent.name:
                        continue
                    implied_paths.append(str(parent / (parent.name + ".toml")))
            # Extend is broken on tomlkit array so do it manually
            for implied_path in implied_paths:
                loaded_info["paths"].append(implied_path)
        root_info = root_cache[root]
        root_relative = full_path.relative_to(root.parent)

        template = list(root.parent.glob("*.template.toml"))
        if not template or len(template) > 1:
            print("No template found for", path)
            continue

        object_type = template[0].name[: -len(".template.toml")]

        try:
            parsed_leaf = tomlkit.parse(full_path.read_text())
        except tomlkit.exceptions.ParseError as error:
            print("Error parsing {}".format(path))
            print(error)
            continue

        comment = tomlkit.comment("Data for path: {}".format(root_relative))
        if len(paths) > 1:
            output_table = tomlkit.table()
            output_table.add(comment)
            output_table.add(tomlkit.nl())
            if object_type not in output_doc:
                output_doc[object_type] = tomlkit.aot()  # short for array of tables
            output_doc[object_type].append(output_table)
        else:
            output_doc.add(comment)
            output_table = output_doc

        # print(path, path.stem, path.parent.stem)
        parsed_path = None
        template_path = None
        for template in root_info["paths"]:
            found = parse.search(template, str(root_relative))
            if found:
                parsed_path = found
                template_path = template
                break

        if parsed_path:
            output_table.add(
                tomlkit.comment("Data inferred from the path: {}".format(template_path))
            )
            for k in parsed_path.named:
                output_table[k] = parsed_path.named[k]

        for parent in reversed(full_path.parents):
            # Skip if the parent is higher than the root.
            if not parent.is_relative_to(root.parent):
                continue
            # Skip if the full_path is a directory toml.
            if parent.stem == full_path.stem:
                continue

            parent_toml = parent / (parent.stem + ".toml")

            if not parent_toml.is_file():
                continue

            parsed_parent = {}
            try:
                parsed_parent = tomlkit.parse(parent_toml.read_text())
            except tomlkit.exceptions.ParseError as error:
                print("Error parsing {}".format(path))
                print(error)
                raise typer.Exit(code=3)

            output_table.add(tomlkit.nl())
            output_table.add(
                tomlkit.comment(
                    "Data from {}".format(parent_toml.relative_to(root.parent))
                )
            )
            for item in parsed_parent.body:
                key, value = item
                output_table.add(key, value)

        output_table.add(tomlkit.nl())
        output_table.add(tomlkit.comment("Data from {}".format(root_relative)))
        for item in parsed_leaf.body:
            key, value = item
            output_table.add(key, value)
    return output_doc


@cascade_app.command()
def files(paths: typing.List[pathlib.Path]):
    """Produce cascaded toml objects for each given path."""
    print("cascade")
    output_doc = _cascade(paths)
    print(tomlkit.dumps(output_doc))


@cascade_app.command()
def filter(
    root: pathlib.Path = typer.Option(
        ".", help="Path to a cascade root. (Where `.cascade.toml` lives.)"
    ),
    filters: typing.List[str] = typer.Argument(
        None, help="TOML values that must match"
    ),
):  # pylint: disable=redefined-builtin
    """Produce cascaded toml objects for each given path."""
    root_toml = root / ".cascade.toml"
    if not root_toml.exists():
        print("Missing root .cascade.toml")
        raise typer.Exit(code=5)

    template = list(root.glob("*.template.toml"))
    if not template or len(template) > 1:
        print("No template found for root", root)
        raise typer.Exit(code=6)

    object_type = template[0].name[: -len(".template.toml")]

    acceptable_values = {}
    for filter_toml in filters:
        parsed = tomlkit.parse(filter_toml)
        for k in parsed:
            if k not in acceptable_values:
                acceptable_values[k] = []
            acceptable_values[k].append(parsed[k])

    output_doc = _cascade(list(root.glob("*/**/*.toml")))

    for i in range(len(output_doc[object_type]) - 1, -1, -1):
        entry = output_doc[object_type][i]
        for k in acceptable_values:
            if k not in entry or entry[k] not in acceptable_values[k]:
                del output_doc[object_type].body[i]

    print(tomlkit.dumps(output_doc))


@app.command()
def check(
    root: pathlib.Path = typer.Option(
        ".", help="Path to a cascade root. (Where `.cascade.toml` lives.)"
    )
):
    """Check that all toml under the given path are parse and match the template."""
    possible_templates = list(root.glob("*.template.toml"))
    if len(possible_templates) > 1:
        print("Only one template supported")
        raise typer.Exit(code=1)
    if not possible_templates:
        print("Template required")
        raise typer.Exit(code=2)
    toml_template = tomlkit.parse(possible_templates[0].read_text())

    error_count = 0
    for tomlfile in root.glob("*/**/*.toml"):
        root_relative = tomlfile.relative_to(root)
        errors = []
        parsed_leaf = {}
        try:
            parsed_leaf = tomlkit.parse(tomlfile.read_text())
        except tomlkit.exceptions.ParseError as error:
            errors.append("Parse error: {}".format(error))
        for k in parsed_leaf:
            # pylint: disable=unidiomatic-typecheck
            if k not in toml_template:
                errors.append("Unknown key {}".format(k))
            elif type(toml_template[k]) != type(parsed_leaf[k]):
                errors.append("Type mismatch for key {}".format(k))
        error_count += len(errors)
        if errors:
            print("Error(s) in {}:".format(root_relative))
            for error in errors:
                print("\t" + error)
            print()

    if error_count > 0:
        raise typer.Exit(code=-1 * error_count)


# Recursion!
def _coalesce(path: pathlib.Path):
    # pylint: disable=too-many-branches
    if path.is_dir():
        shared = None
        for entry in path.iterdir():
            if entry.stem.startswith("."):
                continue
            if entry.stem == path.name:
                continue
            data = _coalesce(entry)
            if data:
                if shared is None:
                    shared = data
                    continue
                different_keys = []
                for k in shared:
                    if k not in data or shared[k] != data[k]:
                        different_keys.append(k)
                for k in different_keys:
                    del shared[k]
            elif data == {}:
                shared = {}
        if not shared:
            return shared
        dir_toml = path / (path.name + ".toml")
        existing = tomlkit.document()
        if dir_toml.exists():
            try:
                existing = tomlkit.parse(dir_toml.read_text())
            except tomlkit.exceptions.ParseError:
                # {} means nothing is shared
                return {}
        for k in shared:
            existing.append(k, shared[k])
        dir_toml.write_text(tomlkit.dumps(existing))
        for entry in path.iterdir():
            if entry.stem.startswith("."):
                continue
            if entry.stem == path.stem:
                continue
            if entry.is_dir():
                entry = entry / (entry.name + ".toml")
            if entry.is_file() and len(entry.suffixes) == 1 and entry.suffix == ".toml":
                existing = tomlkit.parse(entry.read_text())
                for k in shared:
                    if k in existing:
                        del existing[k]
                entry.write_text(tomlkit.dumps(existing))
        return shared

    if path.is_file() and len(path.suffixes) == 1 and path.suffix == ".toml":
        try:
            return tomlkit.parse(path.read_text())
        except tomlkit.exceptions.ParseError:
            # {} means nothing is shared
            return {}
    return None


@refactor_app.command()
def coalesce(
    root: pathlib.Path = typer.Option(
        ".", help="Path to a cascade root. (Where `.cascade.toml` lives.)"
    )
):
    """Move common definitions to shared tomls"""
    _coalesce(root)

def _toml_to_row(path, root_info, headers):
    leaf = tomlkit.parse(path.read_text())

    parsed_path = None
    template_path = None
    for template in reversed(root_info["paths"]):
        found = parse.parse(template, str(path))
        if found:
            parsed_path = found
            template_path = template
            break

    if parsed_path:
        for k in parsed_path.named:
            leaf[k] = parsed_path.named[k]
    row = []
    for header in headers:
        value = None
        if header in leaf:
            value = leaf[header]
        row.append(value)
    return row


def _tabulate(root, root_info, headers, depth=0):
    rows = []
    for p in sorted(root.iterdir()):
        if p.name[0] == ".":
            continue
        if p.is_dir():
            rows.append(_toml_to_row(p / (p.name + ".toml"), root_info, headers))
            rows.extend(_tabulate(p, root_info, headers, depth+1))
        elif depth > 0:
            if p.stem == root.name:
                continue
            rows.append(_toml_to_row(p, root_info, headers))

    return rows

@app.command()
def tabulate(
    root: pathlib.Path = typer.Option(
        ".", help="Path to a cascade root. (Where `.cascade.toml` lives.)"
    ),
    output_format: str = typer.Option(
        "simple", help="tabulate library format or csv"
    ),

    ):
    root_toml = root / ".cascade.toml"
    if not root_toml.exists():
        print("Missing root .cascade.toml")
        raise typer.Exit(code=5)
    root_info = tomlkit.parse(root_toml.read_text())

    template = list(root.glob("*.template.toml"))
    if not template or len(template) > 1:
        print("No template found for root", root)
        raise typer.Exit(code=6)
    toml_template = tomlkit.parse(template[0].read_text())

    implicit_keys = []
    implied_paths = []
    for p in root_info["paths"]:
        implicit_keys.extend(parse.compile(p).named_fields)
        p = pathlib.Path(p)
        for parent in p.parents:
            if not parent.name:
                continue
            implied_paths.append(str(parent / (parent.name + ".toml")))

    # Extend is broken on tomlkit array so do it manually
    for implied_path in implied_paths:
        root_info["paths"].append(implied_path)

    headers = implicit_keys + list(toml_template.keys())

    data = _tabulate(root, root_info, headers)

    if output_format != "csv":
        print(tabulate_lib.tabulate(data, headers=headers, tablefmt=output_format, disable_numparse=True))
    else:
        csvout = csv.writer(sys.stdout)
        csvout.writerow(headers)
        csvout.writerows(data)

if __name__ == "__main__":
    app()
