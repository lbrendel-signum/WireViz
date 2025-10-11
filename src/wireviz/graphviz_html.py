# -*- coding: utf-8 -*-

from typing import Any, List, Optional, Union

from wireviz.data import Color, Image
from wireviz.colors import translate_color
from wireviz.helper import remove_links


def nested_html_table(
    rows: List[Union[str, List[Optional[str]], None]], table_attrs: str = ""
) -> List[str]:
    """Create nested HTML table structure for Graphviz.
    
    Creates a parent table with child tables for list items, allowing independent
    cell widths between rows.
    
    Args:
        rows: List of rows, where each row can be a string (scalar) or a list of
              strings (nested table row). Attributes in leading <tdX> tags are
              injected into the preceding <td> tag.
        table_attrs: Optional attributes for the parent table tag.
    
    Returns:
        List of HTML strings forming the table structure.
    """
    # input: list, each item may be scalar or list
    # output: a parent table with one child table per parent item that is list, and one cell per parent item that is scalar
    # purpose: create the appearance of one table, where cell widths are independent between rows
    # attributes in any leading <tdX> inside a list are injected into to the preceeding <td> tag
    html = []
    html.append(f'<table border="0" cellspacing="0" cellpadding="0"{table_attrs or ""}>')

    num_rows = 0
    for row in rows:
        if isinstance(row, List):
            if len(row) > 0 and any(row):
                html.append(" <tr><td>")
                # fmt: off
                html.append('  <table border="0" cellspacing="0" cellpadding="3" cellborder="1"><tr>')
                # fmt: on
                for cell in row:
                    if cell is not None:
                        # Inject attributes to the preceeding <td> tag where needed
                        # fmt: off
                        html.append(f'   <td balign="left">{cell}</td>'.replace("><tdX", ""))
                        # fmt: on
                html.append("  </tr></table>")
                html.append(" </td></tr>")
                num_rows = num_rows + 1
        elif row is not None:
            html.append(" <tr><td>")
            html.append(f"  {row}")
            html.append(" </td></tr>")
            num_rows = num_rows + 1
    if num_rows == 0:  # empty table
        # generate empty cell to avoid GraphViz errors
        html.append("<tr><td></td></tr>")
    html.append("</table>")
    return html


def html_bgcolor_attr(color: Color) -> str:
    """Return attributes for bgcolor or '' if no color."""
    return f' bgcolor="{translate_color(color, "HEX")}"' if color else ""


def html_bgcolor(color: Color, _extra_attr: str = "") -> str:
    """Return <td> attributes prefix for bgcolor or '' if no color."""
    return f"<tdX{html_bgcolor_attr(color)}{_extra_attr}>" if color else ""


def html_colorbar(color: Color) -> str:
    """Return <tdX> attributes prefix for bgcolor and minimum width or None if no color."""
    return html_bgcolor(color, ' width="4"') if color else None


def html_image(image: Optional[Image]) -> Optional[str]:
    """Generate HTML for an image in Graphviz format.
    
    Args:
        image: Image configuration object.
        
    Returns:
        HTML string with <tdX> tag and image, or None if no image provided.
    """
    if not image:
        return None
    # The leading attributes belong to the preceeding tag. See where used below.
    html = f'{html_size_attr(image)}><img scale="{image.scale}" src="{image.src}"/>'
    if image.fixedsize:
        # Close the preceeding tag and enclose the image cell in a table without
        # borders to avoid narrow borders when the fixed width < the node width.
        html = f""">
    <table border="0" cellspacing="0" cellborder="0"><tr>
     <td{html}</td>
    </tr></table>
   """
    return (
        f"""<tdX{' sides="TLR"' if image.caption else ""}{html_bgcolor_attr(image.bgcolor)}{html}"""
    )


def html_caption(image: Optional[Image]) -> Optional[str]:
    """Generate HTML for an image caption in Graphviz format.
    
    Args:
        image: Image configuration object containing caption text.
        
    Returns:
        HTML string with caption <tdX> tag, or None if no caption.
    """
    return (
        f'<tdX sides="BLR"{html_bgcolor_attr(image.bgcolor)}>{html_line_breaks(image.caption)}'
        if image and image.caption
        else None
    )


def html_size_attr(image: Optional[Image]) -> str:
    """Generate Graphviz HTML attributes for image size.
    
    Args:
        image: Image configuration object with width, height, and fixedsize.
        
    Returns:
        String with width, height, and fixedsize attributes, or empty string.
    """
    # Return Graphviz HTML attributes to specify minimum or fixed size of a TABLE or TD object
    return (
        (
            (f' width="{image.width}"' if image.width else "")
            + (f' height="{image.height}"' if image.height else "")
            + (' fixedsize="true"' if image.fixedsize else "")
        )
        if image
        else ""
    )


def html_line_breaks(inp: Any) -> Any:
    """Convert newlines to HTML line breaks and remove links.
    
    Args:
        inp: Input value, typically a string.
        
    Returns:
        String with newlines replaced by <br /> tags and links removed,
        or unchanged if not a string.
    """
    return remove_links(inp).replace("\n", "<br />") if isinstance(inp, str) else inp
