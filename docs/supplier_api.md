# Supplier API Integration

## Overview

WireViz now supports automatic fetching of additional part information from external supplier APIs (Digikey and Mouser) when partial information is provided in your YAML files.

## Features

- **Automatic Data Enrichment**: When you provide a supplier name and part number (SPN), WireViz can automatically fetch additional information like manufacturer, manufacturer part number (MPN), description, and images.
- **Graceful Degradation**: The tool works normally without API credentials. Supplier data fetching is completely optional.
- **Support for Multiple Suppliers**: Currently supports Digikey and Mouser APIs.

## Configuration

### API Credentials

To use the supplier API integration, you need to configure API credentials via environment variables:

#### Digikey
- `DIGIKEY_CLIENT_ID`: Your Digikey API client ID
- `DIGIKEY_CLIENT_SECRET`: Your Digikey API client secret

Get your Digikey API credentials from: https://developer.digikey.com/

#### Mouser
- `MOUSER_PART_API_KEY`: Your Mouser part search API key

Get your Mouser API key from: https://www.mouser.com/api-hub/

### Setting Environment Variables

**Linux/Mac:**
```bash
export DIGIKEY_CLIENT_ID="your_client_id"
export DIGIKEY_CLIENT_SECRET="your_client_secret"
export MOUSER_PART_API_KEY="your_api_key"
```

**Windows (Command Prompt):**
```cmd
set DIGIKEY_CLIENT_ID=your_client_id
set DIGIKEY_CLIENT_SECRET=your_client_secret
set MOUSER_PART_API_KEY=your_api_key
```

**Windows (PowerShell):**
```powershell
$env:DIGIKEY_CLIENT_ID="your_client_id"
$env:DIGIKEY_CLIENT_SECRET="your_client_secret"
$env:MOUSER_PART_API_KEY="your_api_key"
```

## Usage

### CLI Options

- `--fetch-supplier-data`: Enable fetching additional data from supplier APIs (requires API credentials)
- `--save`: Save enriched data back to the YAML file and download part images to an `images/` folder

### Example YAML with Supplier Information

```yaml
connectors:
  X1:
    type: D-Sub
    subtype: female
    pinlabels: [DCD, RX, TX, DTR, GND, DSR, RTS, CTS, RI]
    supplier: Mouser
    spn: 571-1-1532172-0

  X2:
    type: Molex KK 254
    subtype: female
    pinlabels: [GND, RX, TX]
    supplier: Digikey
    spn: WM4200-ND

cables:
  W1:
    gauge: 0.25 mm2
    length: 0.2
    color_code: DIN
    wirecount: 3
    shield: true

connections:
  -
    - X1: [5,2,3]
    - W1: [1,2,3]
    - X2: [1,3,2]
```

### Basic Usage (No Supplier Data)

Process your file normally without fetching supplier data:

```bash
wireviz myfile.yml
```

### Fetch Supplier Data

Fetch additional information from supplier APIs:

```bash
wireviz myfile.yml --fetch-supplier-data
```

This will fetch additional information like:
- Manufacturer name
- Manufacturer part number (MPN)
- Full part description
- Datasheet URL
- Part image URL

### Save Enriched Data

Save the enriched data back to your YAML file and download part images:

```bash
wireviz myfile.yml --fetch-supplier-data --save
```

This will:
1. Fetch additional information from supplier APIs
2. Update your YAML file with the enriched data
3. Download part images to an `images/` folder next to your YAML file
4. Update the YAML file to reference the local images

## How It Works

1. **Parse YAML**: The tool reads your YAML file and identifies components with `supplier` and `spn` fields.

2. **Fetch Data** (if `--fetch-supplier-data` is enabled):
   - For each component with supplier information, the tool queries the appropriate supplier API
   - The API returns additional information about the part
   - This information is merged with existing data (existing data takes precedence)

3. **Save Data** (if `--save` is enabled):
   - The enriched YAML data is written back to the original file
   - Part images are downloaded to an `images/` folder
   - Image references in the YAML are updated to point to local files

## Supported Suppliers

### Digikey
- API Documentation: https://developer.digikey.com/
- Supported fields: manufacturer, mpn, description, datasheet URL, image URL

### Mouser
- API Documentation: https://www.mouser.com/api-hub/
- Supported fields: manufacturer, mpn, description, datasheet URL, image URL

## Notes

- The tool gracefully handles cases where API credentials are not provided - it simply skips the supplier data fetching step.
- If a part is not found in the supplier's database, the tool will display a warning but continue processing.
- Existing data in your YAML file is never overwritten - fetched data only fills in missing fields.
- The `images/` folder is automatically added to `.gitignore` to prevent committing binary image files.

## Troubleshooting

### "Could not fetch part" warnings

If you see warnings like "Warning: Could not fetch Mouser part XXX-XXX", this could mean:
- The API credentials are not configured
- The API is temporarily unavailable
- The part number is incorrect or not found in the supplier's database
- You don't have an active internet connection

The tool will continue processing without the supplier data.

### API Rate Limits

Both Digikey and Mouser APIs have rate limits. If you're processing many files with many parts, you may hit these limits. The tool will display warnings when API requests fail.
