"""Real-time terminal display for heart rate data."""

import sys
from datetime import datetime
from typing import Optional

from slipstream.garmin.hr_monitor import HeartRateData


class HeartRateDisplay:
    """Real-time terminal display for heart rate monitoring."""

    def __init__(self):
        """Initialize the display."""
        self.measurement_count = 0
        self.session_start: Optional[datetime] = None
        self.last_hr: Optional[int] = None
        self.min_hr: Optional[int] = None
        self.max_hr: Optional[int] = None
        self.hr_sum = 0

    def start_session(self) -> None:
        """Start a new monitoring session."""
        self.session_start = datetime.now()
        self.measurement_count = 0
        self.last_hr = None
        self.min_hr = None
        self.max_hr = None
        self.hr_sum = 0

        self._print_header()

    def _print_header(self) -> None:
        """Print the session header."""
        print("\n" + "=" * 70)
        print("HEART RATE MONITOR - LIVE SESSION")
        print("=" * 70)
        print(f"Started: {self.session_start.strftime('%Y-%m-%d %H:%M:%S')}")
        print("Press Ctrl+C to stop monitoring")
        print("-" * 70)

    def display(self, data: HeartRateData) -> None:
        """Display heart rate measurement.

        Args:
            data: Heart rate data to display
        """
        self.measurement_count += 1
        self.last_hr = data.heart_rate_bpm
        self.hr_sum += data.heart_rate_bpm

        # Update min/max
        if self.min_hr is None or data.heart_rate_bpm < self.min_hr:
            self.min_hr = data.heart_rate_bpm
        if self.max_hr is None or data.heart_rate_bpm > self.max_hr:
            self.max_hr = data.heart_rate_bpm

        # Calculate average
        avg_hr = self.hr_sum / self.measurement_count

        # Build the display line
        time_str = data.timestamp.strftime("%H:%M:%S")
        contact_icon = "●" if data.sensor_contact_detected else "○"

        # Create a simple bar chart visualization
        bar_length = min(data.heart_rate_bpm // 2, 80)  # Scale to fit terminal
        bar = "█" * bar_length

        # Color coding (using ANSI escape codes)
        # Note: These are basic colors, not all terminals support them
        if data.heart_rate_bpm < 60:
            color = "\033[94m"  # Blue - low
        elif data.heart_rate_bpm < 100:
            color = "\033[92m"  # Green - normal
        elif data.heart_rate_bpm < 140:
            color = "\033[93m"  # Yellow - elevated
        else:
            color = "\033[91m"  # Red - high
        reset_color = "\033[0m"

        # Print the measurement
        print(
            f"{time_str} {contact_icon} "
            f"{color}{data.heart_rate_bpm:3d} bpm{reset_color} "
            f"{bar}"
        )

        # Print RR intervals if available (for HRV analysis)
        if data.rr_intervals:
            rr_ms = [int(rr * 1000 / 1024) for rr in data.rr_intervals]
            rr_str = ", ".join(f"{rr}ms" for rr in rr_ms)
            print(f"         RR Intervals: {rr_str}")

        # Flush to ensure immediate display
        sys.stdout.flush()

    def print_summary(self) -> None:
        """Print session summary statistics."""
        if self.session_start is None:
            return

        duration = datetime.now() - self.session_start
        duration_str = str(duration).split(".")[0]  # Remove microseconds

        print("\n" + "-" * 70)
        print("SESSION SUMMARY")
        print("-" * 70)
        print(f"Duration: {duration_str}")
        print(f"Measurements: {self.measurement_count}")

        if self.measurement_count > 0:
            avg_hr = self.hr_sum / self.measurement_count
            print(f"Average HR: {avg_hr:.1f} bpm")
            print(f"Min HR: {self.min_hr} bpm")
            print(f"Max HR: {self.max_hr} bpm")
            print(f"Last HR: {self.last_hr} bpm")

        print("=" * 70 + "\n")
