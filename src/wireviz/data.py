
from dataclasses import dataclass, field
from enum import Enum
from typing import Union

from wireviz.colors import COLOR_CODES, Color, ColorMode, Colors, ColorScheme
from wireviz.helper import aspect_ratio, int2tuple

# Each type alias have their legal values described in comments - validation might be implemented in the future
PlainText = str  # Text not containing HTML tags nor newlines
Hypertext = str  # Text possibly including HTML hyperlinks that are removed in all outputs except HTML output
MultilineHypertext = (
    str  # Hypertext possibly also including newlines to break lines in diagram output
)

Designator = PlainText  # Case insensitive unique name of connector or cable

# Literal type aliases below are commented to avoid requiring python 3.8
ConnectorMultiplier = PlainText  # = Literal['pincount', 'populated', 'unpopulated']
CableMultiplier = PlainText  # = Literal['wirecount', 'terminations', 'length', 'total_length']
ImageScale = PlainText  # = Literal['false', 'true', 'width', 'height', 'both']

# Type combinations
Pin = Union[int, PlainText]  # Pin identifier
PinIndex = int  # Zero-based pin index
Wire = Union[int, PlainText]  # Wire number or Literal['s'] for shield
NoneOrMorePins = Union[Pin, tuple[Pin, ...], None]  # None, one, or a tuple of pin identifiers
NoneOrMorePinIndices = Union[
    PinIndex, tuple[PinIndex, ...], None,
]  # None, one, or a tuple of zero-based pin indices
OneOrMoreWires = Union[Wire, tuple[Wire, ...]]  # One or a tuple of wires

# Metadata can contain whatever is needed by the HTML generation/template.
MetadataKeys = PlainText  # Literal['title', 'description', 'notes', ...]


Side = Enum("Side", "LEFT RIGHT")


class Metadata(dict):
    """Dictionary subclass for storing harness metadata.

    Metadata can contain various keys including 'title', 'description', 'notes', etc.
    All values are used in HTML generation and templating.
    """



@dataclass
class Options:
    """Configuration options for harness diagram generation.

    Attributes:
        fontname: Font name to use in the diagram. Defaults to "arial".
        bgcolor: Background color for the diagram. Defaults to "WH" (white).
        bgcolor_node: Background color for nodes. If None, uses bgcolor.
        bgcolor_connector: Background color for connectors. If None, uses bgcolor_node.
        bgcolor_cable: Background color for cables. If None, uses bgcolor_node.
        bgcolor_bundle: Background color for bundles. If None, uses bgcolor_cable.
        color_mode: Color representation mode. Defaults to "SHORT".
        mini_bom_mode: Whether to use mini BOM mode. Defaults to True.
        template_separator: Separator for template fields. Defaults to ".".

    """

    fontname: PlainText = "arial"
    bgcolor: Color = "WH"
    bgcolor_node: Color | None = "WH"
    bgcolor_connector: Color | None = None
    bgcolor_cable: Color | None = None
    bgcolor_bundle: Color | None = None
    color_mode: ColorMode = "SHORT"
    mini_bom_mode: bool = True
    template_separator: str = "."

    def __post_init__(self) -> None:
        if not self.bgcolor_node:
            self.bgcolor_node = self.bgcolor
        if not self.bgcolor_connector:
            self.bgcolor_connector = self.bgcolor_node
        if not self.bgcolor_cable:
            self.bgcolor_cable = self.bgcolor_node
        if not self.bgcolor_bundle:
            self.bgcolor_bundle = self.bgcolor_cable


@dataclass
class Tweak:
    """Tweaks for customizing Graphviz diagram output.

    Attributes:
        override: Dictionary mapping designators to attribute overrides.
        append: String or list of strings to append to Graphviz output.

    """

    override: dict[Designator, dict[str, str | None]] | None = None
    append: str | list[str] | None = None


@dataclass
class Image:
    """Image configuration for connectors and cables.

    Attributes:
        src: Path to the image file.
        scale: Scaling mode for the image. Can be 'false', 'true', 'width', 'height', or 'both'.
        width: Width in points of the image cell.
        height: Height in points of the image cell.
        fixedsize: Whether to use fixed size for the image cell.
        bgcolor: Background color for the image cell.
        caption: Text caption to display below the image.

    Note:
        See Graphviz HTML documentation at https://graphviz.org/doc/info/shapes.html#html

    """

    # Attributes of the image object <img>:
    src: str
    scale: ImageScale | None = None
    # Attributes of the image cell <td> containing the image:
    width: int | None = None
    height: int | None = None
    fixedsize: bool | None = None
    bgcolor: Color | None = None
    # Contents of the text cell <td> just below the image cell:
    caption: MultilineHypertext | None = None
    # See also HTML doc at https://graphviz.org/doc/info/shapes.html#html

    def __post_init__(self) -> None:
        if self.fixedsize is None:
            # Default True if any dimension specified unless self.scale also is specified.
            self.fixedsize = (self.width or self.height) and self.scale is None

        if self.scale is None:
            if not self.width and not self.height:
                self.scale = "false"
            elif self.width and self.height:
                self.scale = "both"
            else:
                self.scale = "true"  # When only one dimension is specified.

        if self.fixedsize:
            # If only one dimension is specified, compute the other
            # because Graphviz requires both when fixedsize=True.
            if self.height:
                if not self.width:
                    self.width = self.height * aspect_ratio(self.src)
            elif self.width:
                self.height = self.width / aspect_ratio(self.src)


@dataclass
class AdditionalComponent:
    """Additional component to be included in BOM.

    Attributes:
        type: Component type description.
        subtype: Component subtype description.
        manufacturer: Manufacturer name.
        mpn: Manufacturer part number.
        supplier: Supplier name.
        spn: Supplier part number.
        pn: General part number.
        qty: Quantity of the component. Defaults to 1.
        unit: Unit of measurement for quantity.
        qty_multiplier: Multiplier for quantity based on connector/cable properties.
        bgcolor: Background color for the component in diagrams.

    """

    type: MultilineHypertext
    subtype: MultilineHypertext | None = None
    manufacturer: MultilineHypertext | None = None
    mpn: MultilineHypertext | None = None
    supplier: MultilineHypertext | None = None
    spn: MultilineHypertext | None = None
    pn: Hypertext | None = None
    qty: float = 1
    unit: str | None = None
    qty_multiplier: ConnectorMultiplier | CableMultiplier | None = None
    bgcolor: Color | None = None

    @property
    def description(self) -> str:
        t = self.type.rstrip()
        st = f", {self.subtype.rstrip()}" if self.subtype else ""
        return t + st


@dataclass
class Connector:
    """Connector component in a harness.

    Attributes:
        name: Unique designator for the connector.
        bgcolor: Background color for the connector node.
        bgcolor_title: Background color for the connector title.
        manufacturer: Manufacturer name.
        mpn: Manufacturer part number.
        supplier: Supplier name.
        spn: Supplier part number.
        pn: General part number.
        style: Connector style (e.g., 'simple' for single-pin connectors).
        category: Connector category.
        type: Connector type description.
        subtype: Connector subtype description.
        pincount: Number of pins in the connector.
        image: Optional image for the connector.
        notes: Additional notes about the connector.
        pins: List of pin identifiers.
        pinlabels: List of pin labels.
        pincolors: List of pin colors.
        color: Overall connector color.
        show_name: Whether to show the connector name in diagrams.
        show_pincount: Whether to show the pin count in diagrams.
        hide_disconnected_pins: Whether to hide pins with no connections.
        loops: List of pin pairs that form loops.
        ignore_in_bom: Whether to exclude this connector from the BOM.
        additional_components: List of additional components associated with this connector.

    """

    name: Designator
    bgcolor: Color | None = None
    bgcolor_title: Color | None = None
    manufacturer: MultilineHypertext | None = None
    mpn: MultilineHypertext | None = None
    supplier: MultilineHypertext | None = None
    spn: MultilineHypertext | None = None
    pn: Hypertext | None = None
    style: str | None = None
    category: str | None = None
    type: MultilineHypertext | None = None
    subtype: MultilineHypertext | None = None
    pincount: int | None = None
    image: Image | None = None
    notes: MultilineHypertext | None = None
    pins: list[Pin] = field(default_factory=list)
    pinlabels: list[Pin] = field(default_factory=list)
    pincolors: list[Color] = field(default_factory=list)
    color: Color | None = None
    show_name: bool | None = None
    show_pincount: bool | None = None
    hide_disconnected_pins: bool = False
    loops: list[list[Pin]] = field(default_factory=list)
    ignore_in_bom: bool = False
    additional_components: list[AdditionalComponent] = field(default_factory=list)

    def __post_init__(self) -> None:
        if isinstance(self.image, dict):
            self.image = Image(**self.image)

        self.ports_left = False
        self.ports_right = False
        self.visible_pins = {}

        if self.style == "simple":
            if self.pincount and self.pincount > 1:
                raise Exception("Connectors with style set to simple may only have one pin")
            self.pincount = 1

        if not self.pincount:
            self.pincount = max(len(self.pins), len(self.pinlabels), len(self.pincolors))
            if not self.pincount:
                raise Exception(
                    "You need to specify at least one, pincount, pins, pinlabels, or pincolors",
                )

        # create default list for pins (sequential) if not specified
        if not self.pins:
            self.pins = list(range(1, self.pincount + 1))

        if len(self.pins) != len(set(self.pins)):
            raise Exception("Pins are not unique")

        if self.show_name is None:
            # hide designators for simple and for auto-generated connectors by default
            self.show_name = self.style != "simple" and self.name[0:2] != "__"

        if self.show_pincount is None:
            # hide pincount for simple (1 pin) connectors by default
            self.show_pincount = self.style != "simple"

        for loop in self.loops:
            # TODO: allow using pin labels in addition to pin numbers, just like when defining regular connections
            # TODO: include properties of wire used to create the loop
            if len(loop) != 2:
                raise Exception("Loops must be between exactly two pins!")
            for pin in loop:
                if pin not in self.pins:
                    raise Exception(f'Unknown loop pin "{pin}" for connector "{self.name}"!')
                # Make sure loop connected pins are not hidden.
                self.activate_pin(pin, None)

        for i, item in enumerate(self.additional_components):
            if isinstance(item, dict):
                self.additional_components[i] = AdditionalComponent(**item)

    def activate_pin(self, pin: Pin, side: Side) -> None:
        self.visible_pins[pin] = True
        if side == Side.LEFT:
            self.ports_left = True
        elif side == Side.RIGHT:
            self.ports_right = True

    def get_qty_multiplier(self, qty_multiplier: ConnectorMultiplier | None) -> int:
        if not qty_multiplier:
            return 1
        if qty_multiplier == "pincount":
            return self.pincount
        if qty_multiplier == "populated":
            return sum(self.visible_pins.values())
        if qty_multiplier == "unpopulated":
            return max(0, self.pincount - sum(self.visible_pins.values()))
        raise ValueError(f"invalid qty multiplier parameter for connector {qty_multiplier}")


@dataclass
class Cable:
    """Cable or wire bundle in a harness.

    Attributes:
        name: Unique designator for the cable.
        bgcolor: Background color for the cable node.
        bgcolor_title: Background color for the cable title.
        manufacturer: Manufacturer name(s), can be a list for bundles.
        mpn: Manufacturer part number(s), can be a list for bundles.
        supplier: Supplier name(s), can be a list for bundles.
        spn: Supplier part number(s), can be a list for bundles.
        pn: General part number(s), can be a list for bundles.
        category: Cable category (e.g., 'bundle').
        type: Cable type description.
        gauge: Wire gauge value.
        gauge_unit: Unit for wire gauge (e.g., 'AWG', 'mm²').
        show_equiv: Whether to show equivalent gauge in other units.
        length: Cable length.
        length_unit: Unit for cable length (e.g., 'm', 'ft').
        color: Overall cable color.
        wirecount: Number of wires in the cable.
        shield: Whether the cable has a shield, or the shield color.
        image: Optional image for the cable.
        notes: Additional notes about the cable.
        colors: List of wire colors.
        wirelabels: List of wire labels.
        color_code: Standard color code scheme to use.
        show_name: Whether to show the cable name in diagrams.
        show_wirecount: Whether to show the wire count in diagrams.
        show_wirenumbers: Whether to show wire numbers in diagrams.
        ignore_in_bom: Whether to exclude this cable from the BOM.
        additional_components: List of additional components associated with this cable.

    """

    name: Designator
    bgcolor: Color | None = None
    bgcolor_title: Color | None = None
    manufacturer: MultilineHypertext | list[MultilineHypertext] | None = None
    mpn: MultilineHypertext | list[MultilineHypertext] | None = None
    supplier: MultilineHypertext | list[MultilineHypertext] | None = None
    spn: MultilineHypertext | list[MultilineHypertext] | None = None
    pn: Hypertext | list[Hypertext] | None = None
    category: str | None = None
    type: MultilineHypertext | None = None
    gauge: float | None = None
    gauge_unit: str | None = None
    show_equiv: bool = False
    length: float = 0
    length_unit: str | None = None
    color: Color | None = None
    wirecount: int | None = None
    shield: bool | Color = False
    image: Image | None = None
    notes: MultilineHypertext | None = None
    colors: list[Colors] = field(default_factory=list)
    wirelabels: list[Wire] = field(default_factory=list)
    color_code: ColorScheme | None = None
    show_name: bool | None = None
    show_wirecount: bool = True
    show_wirenumbers: bool | None = None
    ignore_in_bom: bool = False
    additional_components: list[AdditionalComponent] = field(default_factory=list)

    def __post_init__(self) -> None:
        if isinstance(self.image, dict):
            self.image = Image(**self.image)

        if isinstance(self.gauge, str):  # gauge and unit specified
            try:
                g, u = self.gauge.split(" ")
            except Exception:
                raise Exception(
                    f"Cable {self.name} gauge={self.gauge} - Gauge must be a number, or number and unit separated by a space",
                )
            self.gauge = g

            if self.gauge_unit is not None:
                pass
            if u.upper() == "AWG":
                self.gauge_unit = u.upper()
            else:
                self.gauge_unit = u.replace("mm2", "mm\u00b2")

        elif self.gauge is not None:  # gauge specified, assume mm2
            if self.gauge_unit is None:
                self.gauge_unit = "mm\u00b2"
        else:
            pass  # gauge not specified

        if isinstance(self.length, str):  # length and unit specified
            try:
                L, u = self.length.split(" ")
                L = float(L)
            except Exception:
                raise Exception(
                    f"Cable {self.name} length={self.length} - Length must be a number, or number and unit separated by a space",
                )
            self.length = L
            if self.length_unit is not None:
                pass
            self.length_unit = u
        elif not isinstance(self.length, (int, float)):
            raise Exception(f"Cable {self.name} length has a non-numeric value")
        elif self.length_unit is None:
            self.length_unit = "m"

        self.connections = []

        if self.wirecount:  # number of wires explicitly defined
            if self.colors:  # use custom color palette (partly or looped if needed)
                pass
            elif self.color_code:
                # use standard color palette (partly or looped if needed)
                if self.color_code not in COLOR_CODES:
                    raise Exception("Unknown color code")
                self.colors = COLOR_CODES[self.color_code]
            else:  # no colors defined, add dummy colors
                self.colors = [""] * self.wirecount

            # make color code loop around if more wires than colors
            if self.wirecount > len(self.colors):
                m = self.wirecount // len(self.colors) + 1
                self.colors = self.colors * int(m)
            # cut off excess after looping
            self.colors = self.colors[: self.wirecount]
        else:  # wirecount implicit in length of color list
            if not self.colors:
                raise Exception(
                    "Unknown number of wires. Must specify wirecount or colors (implicit length)",
                )
            self.wirecount = len(self.colors)

        if self.wirelabels and self.shield and "s" in self.wirelabels:
            raise Exception('"s" may not be used as a wire label for a shielded cable.')

        # if lists of part numbers are provided check this is a bundle and that it matches the wirecount.
        for idfield in [self.manufacturer, self.mpn, self.supplier, self.spn, self.pn]:
            if isinstance(idfield, list):
                if self.category == "bundle":
                    # check the length
                    if len(idfield) != self.wirecount:
                        raise Exception("lists of part data must match wirecount")
                else:
                    raise Exception("lists of part data are only supported for bundles")

        if self.show_name is None:
            # hide designators for auto-generated cables by default
            self.show_name = self.name[0:2] != "__"

        if self.show_wirenumbers is None:
            # by default, show wire numbers for cables, hide for bundles
            self.show_wirenumbers = self.category != "bundle"

        for i, item in enumerate(self.additional_components):
            if isinstance(item, dict):
                self.additional_components[i] = AdditionalComponent(**item)

    # The *_pin arguments accept a tuple, but it seems not in use with the current code.
    def connect(
        self,
        from_name: Designator | None,
        from_pin: NoneOrMorePinIndices,
        via_wire: OneOrMoreWires,
        to_name: Designator | None,
        to_pin: NoneOrMorePinIndices,
    ) -> None:
        from_pin = int2tuple(from_pin)
        via_wire = int2tuple(via_wire)
        to_pin = int2tuple(to_pin)
        if len(from_pin) != len(to_pin):
            raise Exception("from_pin must have the same number of elements as to_pin")
        for i, _ in enumerate(from_pin):
            self.connections.append(
                Connection(from_name, from_pin[i], via_wire[i], to_name, to_pin[i]),
            )

    def get_qty_multiplier(self, qty_multiplier: CableMultiplier | None) -> float:
        if not qty_multiplier:
            return 1
        if qty_multiplier == "wirecount":
            return self.wirecount
        if qty_multiplier == "terminations":
            return len(self.connections)
        if qty_multiplier == "length":
            return self.length
        if qty_multiplier == "total_length":
            return self.length * self.wirecount
        raise ValueError(f"invalid qty multiplier parameter for cable {qty_multiplier}")


@dataclass
class Connection:
    """Connection between a pin and a wire.

    Attributes:
        from_name: Source connector or cable designator.
        from_pin: Source pin identifier.
        via_port: Wire identifier through which the connection passes.
        to_name: Destination connector or cable designator.
        to_pin: Destination pin identifier.

    """

    from_name: Designator | None
    from_pin: Pin | None
    via_port: Wire
    to_name: Designator | None
    to_pin: Pin | None


@dataclass
class MatePin:
    """Direct pin-to-pin mating connection between connectors.

    Attributes:
        from_name: Source connector designator.
        from_pin: Source pin identifier.
        to_name: Destination connector designator.
        to_pin: Destination pin identifier.
        shape: Arrow shape/style for the connection.

    """

    from_name: Designator
    from_pin: Pin
    to_name: Designator
    to_pin: Pin
    shape: str


@dataclass
class MateComponent:
    """Direct component-to-component mating connection.

    Attributes:
        from_name: Source connector designator.
        to_name: Destination connector designator.
        shape: Arrow shape/style for the connection.

    """

    from_name: Designator
    to_name: Designator
    shape: str
