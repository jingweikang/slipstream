"""Heart rate monitor client for Garmin devices using Bluetooth LE."""

import asyncio
from datetime import datetime, timezone
from typing import Callable, Optional

from bleak import BleakClient
from bleak.backends.device import BLEDevice
from pydantic import BaseModel


class HeartRateData(BaseModel):
    """Heart rate measurement data."""

    timestamp: datetime
    heart_rate_bpm: int
    sensor_contact_detected: bool
    energy_expended: Optional[int] = None
    rr_intervals: list[int] = []


class HeartRateMonitor:
    """Monitor heart rate from a Garmin device via BLE."""

    # Standard Bluetooth Heart Rate Service UUID
    HEART_RATE_SERVICE_UUID = "0000180d-0000-1000-8000-00805f9b34fb"
    HEART_RATE_MEASUREMENT_UUID = "00002a37-0000-1000-8000-00805f9b34fb"

    def __init__(self, device: BLEDevice):
        """Initialize heart rate monitor.

        Args:
            device: BLE device to connect to
        """
        self.device = device
        self.client: Optional[BleakClient] = None
        self._data_callback: Optional[Callable[[HeartRateData], None]] = None
        self._is_monitoring = False

    async def connect(self) -> bool:
        """Connect to the device.

        Returns:
            True if connection successful
        """
        try:
            print(f"Connecting to {self.device.name} ({self.device.address})...")
            self.client = BleakClient(self.device.address)
            await self.client.connect()

            if self.client.is_connected:
                print(f"✓ Connected to {self.device.name}")

                # List available services for debugging
                services = self.client.services
                print(f"\nAvailable services ({len(services)}):")
                for service in services:
                    print(f"  - {service.description}: {service.uuid}")
                    for char in service.characteristics:
                        props = ", ".join(char.properties)
                        print(f"    - {char.description}: {char.uuid} ({props})")

                return True
            return False
        except Exception as e:
            print(f"✗ Connection failed: {e}")
            return False

    async def disconnect(self) -> None:
        """Disconnect from the device."""
        if self.client and self.client.is_connected:
            await self.client.disconnect()
            print(f"Disconnected from {self.device.name}")

    def _parse_heart_rate_measurement(self, data: bytearray) -> HeartRateData:
        """Parse heart rate measurement data according to BLE spec.

        Bluetooth Heart Rate Measurement format:
        - Byte 0: Flags
          - Bit 0: Heart Rate Value Format (0 = uint8, 1 = uint16)
          - Bit 1-2: Sensor Contact Status
          - Bit 3: Energy Expended present
          - Bit 4: RR-Interval present
        - Byte 1+: Heart Rate Value
        - Optional: Energy Expended (uint16)
        - Optional: RR-Intervals (uint16 array)

        Args:
            data: Raw measurement data from BLE characteristic

        Returns:
            Parsed heart rate data
        """
        flags = data[0]
        offset = 1

        # Parse heart rate value
        hr_format = flags & 0x01
        if hr_format == 0:
            # uint8 format
            heart_rate = data[offset]
            offset += 1
        else:
            # uint16 format
            heart_rate = int.from_bytes(data[offset : offset + 2], byteorder="little")
            offset += 2

        # Sensor contact status
        sensor_contact_bits = (flags >> 1) & 0x03
        sensor_contact = sensor_contact_bits == 0x03

        # Energy expended
        energy_expended = None
        if flags & 0x08:
            energy_expended = int.from_bytes(data[offset : offset + 2], byteorder="little")
            offset += 2

        # RR intervals (time between heartbeats in 1/1024 second resolution)
        rr_intervals = []
        if flags & 0x10:
            while offset < len(data):
                rr = int.from_bytes(data[offset : offset + 2], byteorder="little")
                rr_intervals.append(rr)
                offset += 2

        return HeartRateData(
            timestamp=datetime.now(timezone.utc),
            heart_rate_bpm=heart_rate,
            sensor_contact_detected=sensor_contact,
            energy_expended=energy_expended,
            rr_intervals=rr_intervals,
        )

    def _handle_notification(self, sender: int, data: bytearray) -> None:
        """Handle incoming heart rate notifications.

        Args:
            sender: Characteristic handle that sent the notification
            data: Raw notification data
        """
        try:
            hr_data = self._parse_heart_rate_measurement(data)
            if self._data_callback:
                self._data_callback(hr_data)
        except Exception as e:
            print(f"Error parsing heart rate data: {e}")

    async def start_monitoring(
        self, callback: Callable[[HeartRateData], None]
    ) -> bool:
        """Start monitoring heart rate.

        Args:
            callback: Function to call with each heart rate measurement

        Returns:
            True if monitoring started successfully
        """
        if not self.client or not self.client.is_connected:
            print("Not connected to device")
            return False

        try:
            self._data_callback = callback
            await self.client.start_notify(
                self.HEART_RATE_MEASUREMENT_UUID, self._handle_notification
            )
            self._is_monitoring = True
            print("✓ Heart rate monitoring started")
            return True
        except Exception as e:
            print(f"✗ Failed to start monitoring: {e}")
            return False

    async def stop_monitoring(self) -> None:
        """Stop monitoring heart rate."""
        if self.client and self.client.is_connected and self._is_monitoring:
            try:
                await self.client.stop_notify(self.HEART_RATE_MEASUREMENT_UUID)
                self._is_monitoring = False
                print("Heart rate monitoring stopped")
            except Exception as e:
                print(f"Error stopping monitoring: {e}")

    @property
    def is_monitoring(self) -> bool:
        """Check if currently monitoring."""
        return self._is_monitoring

    @property
    def is_connected(self) -> bool:
        """Check if connected to device."""
        return self.client is not None and self.client.is_connected
