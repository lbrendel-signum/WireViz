
import base64
import re
from pathlib import Path

mime_subtype_replacements = {"jpg": "jpeg", "tif": "tiff"}


# TODO: Share cache and code between data_URI_base64() and embed_svg_images()
def data_URI_base64(file: str | Path, media: str = "image") -> str:
    """Return Base64-encoded data URI of input file."""
    file = Path(file)
    b64 = base64.b64encode(file.read_bytes()).decode("utf-8")
    uri = f"data:{media}/{get_mime_subtype(file)};base64, {b64}"
    # print(f"data_URI_base64('{file}', '{media}') -> {len(uri)}-character URI")
    if len(uri) > 65535:
        pass
    return uri


def embed_svg_images(svg_in: str, base_path: str | Path = Path.cwd()) -> str:
    """Embed external images in SVG as Base64 data URIs.

    Replaces external image references in SVG with embedded Base64-encoded data URIs.

    Args:
        svg_in: SVG content as a string.
        base_path: Base path for resolving relative image paths. Defaults to current directory.

    Returns:
        SVG content with images embedded as data URIs.

    """
    images_b64 = {}  # cache of base64-encoded images

    def image_tag(pre: str, url: str, post: str) -> str:
        return f'<image{pre} xlink:href="{url}"{post}>'

    def replace(match: re.Match) -> str:
        imgurl = match["URL"]
        if imgurl not in images_b64:  # only encode/cache every unique URL once
            imgurl_abs = (Path(base_path) / imgurl).resolve()
            image = imgurl_abs.read_bytes()
            images_b64[imgurl] = base64.b64encode(image).decode("utf-8")
        return image_tag(
            match["PRE"] or "",
            f"data:image/{get_mime_subtype(imgurl)};base64, {images_b64[imgurl]}",
            match["POST"] or "",
        )

    pattern = re.compile(
        image_tag(r"(?P<PRE> [^>]*?)?", r'(?P<URL>[^"]*?)', r"(?P<POST> [^>]*?)?"),
        re.IGNORECASE,
    )
    return pattern.sub(replace, svg_in)


def get_mime_subtype(filename: str | Path) -> str:
    """Get MIME subtype from filename extension.

    Args:
        filename: Path to file with extension.

    Returns:
        MIME subtype (e.g., 'jpeg' for .jpg files).

    """
    mime_subtype = Path(filename).suffix.lstrip(".").lower()
    if mime_subtype in mime_subtype_replacements:
        mime_subtype = mime_subtype_replacements[mime_subtype]
    return mime_subtype


def embed_svg_images_file(filename_in: str | Path, overwrite: bool = True) -> None:
    """Embed images in an SVG file and optionally overwrite the original.

    Args:
        filename_in: Path to input SVG file.
        overwrite: If True, replaces the original file. If False, creates a .b64.svg file.

    """
    filename_in = Path(filename_in).resolve()
    filename_out = filename_in.with_suffix(".b64.svg")
    filename_out.write_text(  # TODO?: Verify xml encoding="utf-8" in SVG?
        embed_svg_images(filename_in.read_text(), filename_in.parent),
    )  # TODO: Use encoding="utf-8" in both read_text() and write_text()
    if overwrite:
        filename_out.replace(filename_in)
