"""BLE device scanner for discovering Garmin devices."""

import asyncio
from typing import Optional

from bleak import BleakScanner
from bleak.backends.device import BLEDevice


class GarminDeviceScanner:
    """Scanner for discovering Garmin devices via Bluetooth Low Energy."""

    GARMIN_NAME_PREFIXES = ["Garmin", "GARMIN", "HRM-"]
    SCAN_DURATION = 10.0  # seconds

    async def scan(self, timeout: float = SCAN_DURATION) -> list[BLEDevice]:
        """Scan for available Garmin devices.

        Args:
            timeout: How long to scan for devices in seconds

        Returns:
            List of discovered Garmin BLE devices
        """
        print(f"Scanning for Garmin devices for {timeout} seconds...")
        devices = await BleakScanner.discover(timeout=timeout)

        garmin_devices = [
            device
            for device in devices
            if device.name
            and any(device.name.startswith(prefix) for prefix in self.GARMIN_NAME_PREFIXES)
        ]

        return garmin_devices

    async def scan_and_select(self) -> Optional[BLEDevice]:
        """Scan for Garmin devices and let user select one.

        Returns:
            Selected BLE device or None if no devices found or cancelled
        """
        devices = await self.scan()

        if not devices:
            print("No Garmin devices found.")
            print("\nTroubleshooting:")
            print("1. Make sure your Garmin watch is in pairing/broadcast mode")
            print("2. Ensure Bluetooth is enabled on your Mac")
            print("3. Check that the watch is not already connected to another device")
            return None

        print(f"\nFound {len(devices)} Garmin device(s):")
        for idx, device in enumerate(devices, 1):
            rssi_info = f" (RSSI: {device.rssi} dBm)" if device.rssi else ""
            print(f"{idx}. {device.name} - {device.address}{rssi_info}")

        if len(devices) == 1:
            print(f"\nAuto-selecting the only device: {devices[0].name}")
            return devices[0]

        while True:
            try:
                selection = input(
                    f"\nSelect device (1-{len(devices)}) or 'q' to quit: "
                ).strip()

                if selection.lower() == "q":
                    return None

                idx = int(selection)
                if 1 <= idx <= len(devices):
                    return devices[idx - 1]
                else:
                    print(f"Please enter a number between 1 and {len(devices)}")
            except ValueError:
                print("Please enter a valid number or 'q'")
            except KeyboardInterrupt:
                print("\nCancelled.")
                return None
