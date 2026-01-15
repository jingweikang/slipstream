# Garmin Heart Rate Monitor

Live heart rate monitoring from Garmin devices via Bluetooth Low Energy.

## Features

- Real-time heart rate monitoring from Garmin watches
- Live terminal display with color-coded HR zones
- Automatic recording to Parquet files
- RR interval capture for HRV analysis
- Session statistics and summaries

## Requirements

- macOS (tested), Linux, or Windows
- Python 3.11+
- Bluetooth enabled
- Garmin watch that supports Bluetooth heart rate broadcasting

## Installation

Install the required dependencies:

```bash
poetry install
```

This will install the `bleak` library for Bluetooth Low Energy support.

## Usage

### Basic Heart Rate Monitoring

Start monitoring with real-time display and recording:

```bash
poetry run python scripts/cli.py garmin-hr-monitor
```

This will:
1. Scan for Garmin devices (10 seconds)
2. Let you select a device if multiple are found
3. Connect to the device
4. Start monitoring and displaying heart rate
5. Record data to `data/garmin/hr_session_TIMESTAMP.parquet`

### Monitor Without Recording

Display heart rate in real-time without saving to file:

```bash
poetry run python scripts/cli.py garmin-hr-monitor --no-record
```

### Custom Options

```bash
# Custom output directory
poetry run python scripts/cli.py garmin-hr-monitor --output-dir my_data/hr

# Longer scan time (useful if watch is slow to appear)
poetry run python scripts/cli.py garmin-hr-monitor --scan-timeout 15
```

## Preparing Your Garmin Watch

Before running the monitor, you need to enable heart rate broadcasting on your Garmin watch:

### For Most Garmin Watches:

1. Go to **Settings** on your watch
2. Navigate to **Sensors & Accessories**
3. Select **Heart Rate**
4. Enable **Broadcast Heart Rate** or **Broadcast During Activity**

### Alternative Method (During Activity):

1. Start an activity on your watch
2. Swipe down to access settings
3. Enable **Broadcast Heart Rate**

Once broadcasting is enabled, the watch will appear as a Bluetooth device that can be discovered by the scanner.

## Understanding the Display

The live display shows:

```
17:32:45 ● 142 bpm ████████████████████████████████████████████████████████████████████████
```

- **Time**: Current time of measurement
- **●/○**: Sensor contact detected (filled/empty circle)
- **BPM**: Heart rate in beats per minute
- **Bar**: Visual representation of heart rate
- **Color coding**:
  - Blue: < 60 bpm (resting)
  - Green: 60-99 bpm (normal)
  - Yellow: 100-139 bpm (elevated)
  - Red: ≥ 140 bpm (high intensity)

If RR intervals are available (for heart rate variability), they'll be displayed below each measurement:
```
         RR Intervals: 847ms, 832ms, 856ms
```

## Session Summary

When you stop monitoring (Ctrl+C), you'll see a summary:

```
SESSION SUMMARY
----------------------------------------------------------------------
Duration: 0:15:32
Measurements: 932
Average HR: 128.4 bpm
Min HR: 98 bpm
Max HR: 165 bpm
Last HR: 132 bpm
```

## Data Format

Heart rate data is saved in Parquet format with the following schema:

| Column | Type | Description |
|--------|------|-------------|
| `timestamp` | datetime | UTC timestamp of measurement |
| `heart_rate_bpm` | int | Heart rate in beats per minute |
| `sensor_contact_detected` | bool | Whether watch detected skin contact |
| `energy_expended` | int (optional) | Cumulative energy in kilojoules |
| `rr_intervals` | list[int] (optional) | RR intervals in 1/1024 second units |
| `mean_rr_interval_ms` | float (optional) | Mean RR interval in milliseconds |

## Analyzing Recorded Data

You can query the recorded Parquet files using DuckDB:

```python
import duckdb

# Load a session
df = duckdb.query("SELECT * FROM 'data/garmin/hr_session_20260115_173000.parquet'").df()

# Calculate HR zones
print(df['heart_rate_bpm'].describe())

# Plot HR over time
import matplotlib.pyplot as plt
df.plot(x='timestamp', y='heart_rate_bpm')
plt.show()
```

Or use pandas directly:

```python
import pandas as pd

df = pd.read_parquet('data/garmin/hr_session_20260115_173000.parquet')
print(df.head())
```

## Troubleshooting

### No devices found

- Ensure your Garmin watch has heart rate broadcasting enabled
- Make sure Bluetooth is enabled on your Mac
- Check that the watch isn't already connected to another device
- Try moving the watch closer to your computer
- Restart Bluetooth on your Mac: System Settings → Bluetooth → turn off/on

### Connection failed

- The watch may have gone to sleep - wake it up and enable broadcasting again
- Try forgetting the device in Bluetooth settings and reconnecting
- Restart your watch
- Check that you have the latest firmware on your watch

### Lost connection during monitoring

- Keep the watch within Bluetooth range (typically 10 meters / 30 feet)
- Ensure the watch battery isn't critically low
- The watch may have automatically stopped broadcasting after a timeout

### Permission errors (macOS)

If you get Bluetooth permission errors, grant terminal/Python access:
- Go to System Settings → Privacy & Security → Bluetooth
- Add Terminal or your Python executable to the allowed apps

## Technical Details

### Bluetooth Specifications

This implementation uses the standard Bluetooth Heart Rate Service (HRS):
- Service UUID: `0000180d-0000-1000-8000-00805f9b34fb`
- Characteristic UUID: `00002a37-0000-1000-8000-00805f9b34fb`

The heart rate measurement follows the Bluetooth SIG specification with support for:
- Variable format (uint8 or uint16)
- Sensor contact detection
- Energy expended tracking
- RR interval measurements (for HRV)

### Performance

- Typical measurement frequency: 1 Hz (one measurement per second)
- Some watches may provide measurements more frequently during activity
- RR intervals are typically provided at the native sampling rate

## Future Enhancements

Potential improvements:
- Multi-sensor support (power meter, cadence, speed)
- Real-time workout guidance based on HR zones
- Integration with Strava activities
- ANT+ support for multi-device connectivity
- Live visualization web dashboard
