import os
import sys
from pathlib import Path

import typer
import yaml
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

if __name__ == "__main__":
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import wireviz.wireviz as wv
from wireviz import APP_NAME, __version__
from wireviz.helper import file_read_text
from wireviz.suppliers import get_supplier_manager

# Global console for rich output
console = Console()

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


def save_enriched_yaml(yaml_path: Path, yaml_data: dict, download_images: bool = True) -> None:
    """Save enriched YAML data back to file and optionally download part images.

    Args:
        yaml_path: Path to the original YAML file
        yaml_data: Enriched YAML data dictionary
        download_images: Whether to download part images to images/ folder
    """
    # Create images directory if needed
    images_dir = yaml_path.parent / "images"
    
    if download_images:
        supplier_manager = get_supplier_manager()
        
        # Process connectors
        for key, attribs in yaml_data.get("connectors", {}).items():
            image_url = attribs.get("_image_url")
            if image_url:
                # Generate image filename from key and URL
                image_ext = Path(image_url).suffix or ".jpg"
                image_filename = f"{key}_part{image_ext}"
                image_path = images_dir / image_filename
                
                if supplier_manager.download_image(image_url, image_path):
                    # Update YAML to reference local image
                    if "image" not in attribs:
                        attribs["image"] = {}
                    if isinstance(attribs["image"], dict):
                        attribs["image"]["src"] = f"images/{image_filename}"
                
                # Remove temporary URL fields
                del attribs["_image_url"]
            
            # Clean up other temporary fields
            if "_datasheet_url" in attribs:
                del attribs["_datasheet_url"]
        
        # Process cables
        for key, attribs in yaml_data.get("cables", {}).items():
            image_url = attribs.get("_image_url")
            if image_url:
                image_ext = Path(image_url).suffix or ".jpg"
                image_filename = f"{key}_part{image_ext}"
                image_path = images_dir / image_filename
                
                if supplier_manager.download_image(image_url, image_path):
                    if "image" not in attribs:
                        attribs["image"] = {}
                    if isinstance(attribs["image"], dict):
                        attribs["image"]["src"] = f"images/{image_filename}"
                
                del attribs["_image_url"]
            
            if "_datasheet_url" in attribs:
                del attribs["_datasheet_url"]
        
        # Process additional_bom_items
        for item in yaml_data.get("additional_bom_items", []):
            if "_image_url" in item:
                del item["_image_url"]
            if "_datasheet_url" in item:
                del item["_datasheet_url"]
    else:
        # Just clean up temporary fields without downloading
        for section in ["connectors", "cables"]:
            for attribs in yaml_data.get(section, {}).values():
                attribs.pop("_image_url", None)
                attribs.pop("_datasheet_url", None)
        
        for item in yaml_data.get("additional_bom_items", []):
            item.pop("_image_url", None)
            item.pop("_datasheet_url", None)
    
    # Save enriched YAML back to file
    with open(yaml_path, "w", encoding="utf-8") as f:
        yaml.dump(yaml_data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)



def wireviz(
    file: list[str],
    output_name: str | None = None,
    format: str | None = "hpst",
    prepend: list[str] | None = None,
    output_dir: Path | None = None,
    version: bool | None = False,
    quiet: bool | None = False,
    save: bool | None = False,
    fetch_supplier_data: bool | None = False,
) -> None:
    """
    Parses the provided FILE and generates the specified outputs.
    
    Args:
        file: Input YAML file(s) to process
        output_name: Name for output files
        format: Output format codes (h=html, p=png, s=svg, t=tsv)
        prepend: Files to prepend to input
        output_dir: Directory for output files
        version: Show version and exit
        quiet: Suppress progress output
        save: Save enriched data back to YAML file
        fetch_supplier_data: Fetch additional data from supplier APIs
    """
    if not quiet:
        console.print(f"\n[bold cyan]{APP_NAME}[/bold cyan] [cyan]{__version__}[/cyan]")
    else:
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
    if prepend and len(prepend) > 0:
        prepend_input = ""
        for prepend_file in prepend:
            prepend_file = Path(prepend_file)
            if not prepend_file.exists():
                raise Exception(f"File does not exist:\n{prepend_file}")
            if not quiet:
                console.print(f"[dim]Prepend file: {prepend_file}[/dim]")
            else:
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

        if not quiet:
            console.print(f"\n[bold]Processing:[/bold] [green]{f}[/green]")
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
                transient=True,
            ) as progress:
                task1 = progress.add_task("[cyan]Parsing input file...", total=None)
                yaml_input = file_read_text(f)
                file_dir = f.parent

                yaml_input = prepend_input + yaml_input
                image_paths = {file_dir}
                if prepend:
                    for p in prepend:
                        if p:  # Only add non-empty prepend paths
                            image_paths.add(Path(p).parent)

                # If saving is enabled, parse YAML separately to get enriched data
                yaml_data_dict = None
                if save or fetch_supplier_data:
                    yaml_data_dict = yaml.safe_load(yaml_input)

                progress.update(task1, description="[cyan]Building harness connections...")

                wv.parse(
                    yaml_data_dict if yaml_data_dict else yaml_input,
                    output_formats=output_formats,
                    output_dir=_output_dir,
                    output_name=_output_name,
                    image_paths=list(image_paths),
                    fetch_supplier_data=fetch_supplier_data,
                )

                # Save enriched data back to YAML if requested
                if save and yaml_data_dict:
                    progress.update(task1, description="[cyan]Saving enriched YAML...")
                    save_enriched_yaml(f, yaml_data_dict, download_images=True)

                progress.update(task1, description="[green]✓ Complete")

            # Show individual output files
            console.print("[dim]Generated files:[/dim]")
            for fmt in output_formats:
                if fmt == "tsv":
                    output_path = Path(_output_dir) / f"{_output_name}.bom.{fmt}"
                else:
                    output_path = Path(_output_dir) / f"{_output_name}.{fmt}"
                console.print(f"  [dim]→[/dim] {output_path}")
            
            if save:
                console.print(f"  [dim]→[/dim] {f} (enriched)")
                if (f.parent / "images").exists():
                    console.print(f"  [dim]→[/dim] {f.parent / 'images'}/ (part images)")
        else:
            print("Input file:  ", f)
            print("Output file: ", f"{Path(_output_dir / _output_name)}.{output_formats_str}")

            yaml_input = file_read_text(f)
            file_dir = f.parent

            yaml_input = prepend_input + yaml_input
            image_paths = {file_dir}
            if prepend:
                for p in prepend:
                    if p:  # Only add non-empty prepend paths
                        image_paths.add(Path(p).parent)

            # If saving is enabled, parse YAML separately to get enriched data
            yaml_data_dict = None
            if save or fetch_supplier_data:
                yaml_data_dict = yaml.safe_load(yaml_input)

            wv.parse(
                yaml_data_dict if yaml_data_dict else yaml_input,
                output_formats=output_formats,
                output_dir=_output_dir,
                output_name=_output_name,
                image_paths=list(image_paths),
                fetch_supplier_data=fetch_supplier_data,
            )

            # Save enriched data back to YAML if requested
            if save and yaml_data_dict:
                save_enriched_yaml(f, yaml_data_dict, download_images=True)
                print("Saved enriched YAML:", f)

    if quiet:
        print()

def main():
    typer.run(wireviz)

if __name__ == "__main__":
    main()
