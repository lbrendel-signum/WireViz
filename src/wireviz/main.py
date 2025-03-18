# -*- coding: utf-8 -*-

import os
import sys
from pathlib import Path
from typing import Optional

import typer

if __name__ == "__main__":
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import wireviz.wireviz as wv
from wireviz import APP_NAME, __version__
from wireviz.wv_helper import file_read_text

app = typer.Typer()

format_codes = {
    # "c": "csv",
    "g": "gv",
    "h": "html",
    "p": "png",
    # "P": "pdf",
    "s": "svg",
    "t": "tsv",
}


def wireviz(
    file: list[str],
    output_name: Optional[str] = None,
    format: Optional[str] = "hpst",
    prepend: Optional[list[str]] = None,
    output_dir: Optional[Path] = ".\\",
    version: Optional[bool] = False,
):
    """
    Parses the provided FILE and generates the specified outputs.
    """
    print()
    print(f"{APP_NAME} {__version__}")
    if version:
        return  # print version number only and exit

    # get list of files
    try:
        _ = iter(file)
    except TypeError:
        filepaths = [file]
    else:
        filepaths = list(file)

    # determine output formats
    output_formats = []
    for code in format:
        if code in format_codes:
            output_formats.append(format_codes[code])
        else:
            raise Exception(f"Unknown output format: {code}")
    output_formats = tuple(sorted(set(output_formats)))
    output_formats_str = (
        f"[{'|'.join(output_formats)}]" if len(output_formats) > 1 else output_formats[0]
    )

    # check prepend file
    if len(prepend) > 0:
        prepend_input = ""
        for prepend_file in prepend:
            prepend_file = Path(prepend_file)
            if not prepend_file.exists():
                raise Exception(f"File does not exist:\n{prepend_file}")
            print("Prepend file:", prepend_file)

            prepend_input += file_read_text(prepend_file) + "\n"
    else:
        prepend_input = ""

    # run WireVIz on each input file
    for fi in filepaths:
        f = Path(fi)
        if not f.exists():
            raise Exception(f"File does not exist:\n{f}")

        # file_out = file.with_suffix("") if not output_file else output_file
        _output_dir = f.parent if not output_dir else output_dir
        _output_name = f.stem if not output_name else output_name

        print("Input file:  ", f)
        print("Output file: ", f"{Path(_output_dir / _output_name)}.{output_formats_str}")

        yaml_input = file_read_text(f)
        file_dir = f.parent

        yaml_input = prepend_input + yaml_input
        image_paths = {file_dir}
        for p in prepend:
            image_paths.add(Path(p).parent)

        wv.parse(
            yaml_input,
            output_formats=output_formats,
            output_dir=_output_dir,
            output_name=_output_name,
            image_paths=list(image_paths),
        )

    print()


if __name__ == "__main__":
    typer.run(wireviz)
