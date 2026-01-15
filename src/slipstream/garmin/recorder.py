"""Heart rate data recorder for saving to Parquet files."""

from datetime import datetime
from pathlib import Path
from typing import Optional

import pandas as pd

from slipstream.garmin.hr_monitor import HeartRateData


class HeartRateRecorder:
    """Records heart rate data to Parquet files."""

    def __init__(self, output_dir: Path = Path("data/garmin")):
        """Initialize the recorder.

        Args:
            output_dir: Directory to save Parquet files
        """
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.session_start: Optional[datetime] = None
        self.session_file: Optional[Path] = None
        self.measurements: list[dict] = []

    def start_session(self) -> Path:
        """Start a new recording session.

        Returns:
            Path to the session file that will be created
        """
        self.session_start = datetime.now()
        timestamp = self.session_start.strftime("%Y%m%d_%H%M%S")
        self.session_file = self.output_dir / f"hr_session_{timestamp}.parquet"
        self.measurements = []

        print(f"Recording to: {self.session_file}")
        return self.session_file

    def record(self, data: HeartRateData) -> None:
        """Record a heart rate measurement.

        Args:
            data: Heart rate data to record
        """
        # Convert to dict for DataFrame
        measurement = {
            "timestamp": data.timestamp,
            "heart_rate_bpm": data.heart_rate_bpm,
            "sensor_contact_detected": data.sensor_contact_detected,
            "energy_expended": data.energy_expended,
        }

        # Add RR intervals as separate columns if present
        if data.rr_intervals:
            # Store RR intervals as a JSON-compatible list
            measurement["rr_intervals"] = data.rr_intervals
            # Also calculate mean RR interval in milliseconds for convenience
            rr_ms = [int(rr * 1000 / 1024) for rr in data.rr_intervals]
            measurement["mean_rr_interval_ms"] = sum(rr_ms) / len(rr_ms)
        else:
            measurement["rr_intervals"] = None
            measurement["mean_rr_interval_ms"] = None

        self.measurements.append(measurement)

    def save(self) -> Optional[Path]:
        """Save recorded measurements to Parquet file.

        Returns:
            Path to saved file, or None if no measurements
        """
        if not self.measurements:
            print("No measurements to save")
            return None

        if self.session_file is None:
            print("No active session")
            return None

        # Create DataFrame
        df = pd.DataFrame(self.measurements)

        # Save to Parquet
        df.to_parquet(self.session_file, index=False, engine="pyarrow")

        file_size = self.session_file.stat().st_size
        print(f"\n✓ Saved {len(self.measurements)} measurements to {self.session_file}")
        print(f"  File size: {file_size:,} bytes")

        return self.session_file

    def get_stats(self) -> dict:
        """Get statistics about the current recording session.

        Returns:
            Dictionary of session statistics
        """
        if not self.measurements:
            return {}

        df = pd.DataFrame(self.measurements)

        duration = (
            df["timestamp"].max() - df["timestamp"].min()
            if len(df) > 1
            else pd.Timedelta(0)
        )

        return {
            "session_start": self.session_start,
            "measurement_count": len(self.measurements),
            "duration": duration,
            "mean_hr": df["heart_rate_bpm"].mean(),
            "min_hr": df["heart_rate_bpm"].min(),
            "max_hr": df["heart_rate_bpm"].max(),
            "std_hr": df["heart_rate_bpm"].std(),
        }
