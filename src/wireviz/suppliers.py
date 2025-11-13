"""Supplier API integration for fetching additional part information.

This module provides integration with external supplier APIs (Digikey, Mouser)
to automatically fetch additional part information when partial data is provided.
"""

import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import requests


@dataclass
class SupplierConfig:
    """Configuration for supplier API credentials.

    Credentials are loaded from environment variables:
    - DIGIKEY_CLIENT_ID, DIGIKEY_CLIENT_SECRET for Digikey
    - MOUSER_API_KEY for Mouser
    """

    digikey_client_id: str | None = None
    digikey_client_secret: str | None = None
    mouser_api_key: str | None = None

    @classmethod
    def from_environment(cls) -> "SupplierConfig":
        """Load supplier credentials from environment variables."""
        return cls(
            digikey_client_id=os.environ.get("DIGIKEY_CLIENT_ID"),
            digikey_client_secret=os.environ.get("DIGIKEY_CLIENT_SECRET"),
            mouser_api_key=os.environ.get("MOUSER_API_KEY"),
        )

    def has_digikey_credentials(self) -> bool:
        """Check if Digikey credentials are configured."""
        return bool(self.digikey_client_id and self.digikey_client_secret)

    def has_mouser_credentials(self) -> bool:
        """Check if Mouser credentials are configured."""
        return bool(self.mouser_api_key)


@dataclass
class PartInfo:
    """Information fetched from supplier API."""

    manufacturer: str | None = None
    mpn: str | None = None
    description: str | None = None
    image_url: str | None = None
    datasheet_url: str | None = None
    supplier: str | None = None
    spn: str | None = None

    def merge_with_existing(self, existing_data: dict[str, Any]) -> dict[str, Any]:
        """Merge fetched data with existing data, preserving existing values."""
        merged = existing_data.copy()

        # Only update fields that are not already present
        if not merged.get("manufacturer") and self.manufacturer:
            merged["manufacturer"] = self.manufacturer
        if not merged.get("mpn") and self.mpn:
            merged["mpn"] = self.mpn
        if not merged.get("supplier") and self.supplier:
            merged["supplier"] = self.supplier
        if not merged.get("spn") and self.spn:
            merged["spn"] = self.spn

        # Store additional metadata if not present
        if not merged.get("description") and self.description:
            merged["description"] = self.description

        # Store image and datasheet URLs for potential download
        if self.image_url:
            merged["_image_url"] = self.image_url
        if self.datasheet_url:
            merged["_datasheet_url"] = self.datasheet_url

        return merged


class SupplierClient(ABC):
    """Abstract base class for supplier API clients."""

    @abstractmethod
    def search_part(self, spn: str) -> PartInfo | None:
        """Search for a part by supplier part number."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if the client has valid credentials and can make requests."""
        pass


class DigikeyClient(SupplierClient):
    """Client for Digikey API."""

    def __init__(self, client_id: str | None, client_secret: str | None):
        self.client_id = client_id
        self.client_secret = client_secret
        self._api_available = False
        self._client = None

        if self.is_available():
            try:
                # Import digikey-api library if credentials are available
                import digikey

                self._client = digikey
                self._api_available = True
            except ImportError:
                # Library not installed, will be unavailable
                pass

    def is_available(self) -> bool:
        """Check if Digikey client is available."""
        return bool(self.client_id and self.client_secret)

    def search_part(self, spn: str) -> PartInfo | None:
        """Search for a part by Digikey part number.

        Args:
            spn: Supplier part number (Digikey part number)

        Returns:
            PartInfo object with fetched data, or None if not found or unavailable
        """
        if not self._api_available or not self._client:
            return None

        try:
            # Configure API credentials
            os.environ["DIGIKEY_CLIENT_ID"] = self.client_id
            os.environ["DIGIKEY_CLIENT_SECRET"] = self.client_secret

            # Search for the part
            part = self._client.product_details(spn)

            if part:
                return PartInfo(
                    manufacturer=getattr(part, "manufacturer", {}).get("value") if hasattr(part, "manufacturer") else None,
                    mpn=getattr(part, "manufacturer_part_number", None) if hasattr(part, "manufacturer_part_number") else None,
                    description=getattr(part, "product_description", None) if hasattr(part, "product_description") else None,
                    image_url=getattr(part, "primary_photo", None) if hasattr(part, "primary_photo") else None,
                    datasheet_url=getattr(part, "primary_datasheet", None) if hasattr(part, "primary_datasheet") else None,
                    supplier="Digikey",
                    spn=spn,
                )
        except Exception as e:
            # Silently fail - API might be unavailable or part not found
            print(f"Warning: Could not fetch Digikey part {spn}: {e}")

        return None


class MouserClient(SupplierClient):
    """Client for Mouser API."""

    def __init__(self, api_key: str | None):
        self.api_key = api_key
        self._api_available = False
        self._client = None

        if self.is_available():
            try:
                # Import mouser-api library if credentials are available
                import mouser

                self._client = mouser
                self._api_available = True
            except ImportError:
                # Library not installed, will be unavailable
                pass

    def is_available(self) -> bool:
        """Check if Mouser client is available."""
        return bool(self.api_key)

    def search_part(self, spn: str) -> PartInfo | None:
        """Search for a part by Mouser part number.

        Args:
            spn: Supplier part number (Mouser part number)

        Returns:
            PartInfo object with fetched data, or None if not found or unavailable
        """
        if not self._api_available or not self._client:
            return None

        try:
            # Configure API key
            os.environ["MOUSER_API_KEY"] = self.api_key

            # Search for the part
            part = self._client.part_search(spn)

            if part and hasattr(part, "parts") and part.parts:
                first_part = part.parts[0]
                return PartInfo(
                    manufacturer=getattr(first_part, "manufacturer", None) if hasattr(first_part, "manufacturer") else None,
                    mpn=getattr(first_part, "manufacturer_part_number", None) if hasattr(first_part, "manufacturer_part_number") else None,
                    description=getattr(first_part, "description", None) if hasattr(first_part, "description") else None,
                    image_url=getattr(first_part, "image_url", None) if hasattr(first_part, "image_url") else None,
                    datasheet_url=getattr(first_part, "datasheet_url", None) if hasattr(first_part, "datasheet_url") else None,
                    supplier="Mouser",
                    spn=spn,
                )
        except Exception as e:
            # Silently fail - API might be unavailable or part not found
            print(f"Warning: Could not fetch Mouser part {spn}: {e}")

        return None


class SupplierManager:
    """Manager for coordinating multiple supplier API clients."""

    def __init__(self, config: SupplierConfig | None = None):
        """Initialize supplier manager with configuration.

        Args:
            config: SupplierConfig object. If None, loads from environment.
        """
        if config is None:
            config = SupplierConfig.from_environment()

        self.config = config
        self.digikey = DigikeyClient(config.digikey_client_id, config.digikey_client_secret)
        self.mouser = MouserClient(config.mouser_api_key)

    def is_any_supplier_available(self) -> bool:
        """Check if any supplier API is available."""
        return self.digikey.is_available() or self.mouser.is_available()

    def fetch_part_info(
        self, supplier: str | None, spn: str | None, existing_data: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Fetch part information from supplier API.

        Args:
            supplier: Supplier name (case-insensitive, e.g., "Digikey", "Mouser")
            spn: Supplier part number
            existing_data: Existing component data to merge with

        Returns:
            Dictionary with merged component data including fetched information
        """
        if existing_data is None:
            existing_data = {}

        # If no supplier or spn provided, return existing data unchanged
        if not supplier or not spn:
            return existing_data

        # Normalize supplier name
        supplier_lower = supplier.lower()

        # Try to fetch from appropriate supplier
        part_info = None
        if supplier_lower in ("digikey", "digi-key"):
            if self.digikey.is_available():
                part_info = self.digikey.search_part(spn)
        elif supplier_lower == "mouser":
            if self.mouser.is_available():
                part_info = self.mouser.search_part(spn)

        # Merge fetched data with existing data
        if part_info:
            return part_info.merge_with_existing(existing_data)

        return existing_data

    def download_image(self, image_url: str, output_path: Path) -> bool:
        """Download an image from URL to the specified path.

        Args:
            image_url: URL of the image to download
            output_path: Path where the image should be saved

        Returns:
            True if download was successful, False otherwise
        """
        try:
            response = requests.get(image_url, timeout=30)
            response.raise_for_status()

            # Create parent directory if it doesn't exist
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Write image data to file
            output_path.write_bytes(response.content)
            return True
        except Exception as e:
            print(f"Warning: Could not download image from {image_url}: {e}")
            return False


# Global supplier manager instance (lazy initialized)
_supplier_manager: SupplierManager | None = None


def get_supplier_manager() -> SupplierManager:
    """Get the global supplier manager instance."""
    global _supplier_manager
    if _supplier_manager is None:
        _supplier_manager = SupplierManager()
    return _supplier_manager
