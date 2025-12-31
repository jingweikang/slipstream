# slipstream
Cycling Data Analysis Project

## Goal
Build a system to analyze cycling performance data and detect fatigue patterns during efforts, with a focus on improving FTP and pacing strategy.

## Project Phases

### Phase 0: Setup & Authentication
- [ ] Register application with Strava API
- [ ] Implement OAuth flow to access personal data
- [ ] Test API connectivity and rate limits

### Phase 1: Data Ingestion & Storage

#### Phase 1a: Historical Data Backfill
- [ ] Fetch all historical activities from Strava API
- [ ] Download detailed stream data (HR, power, cadence, altitude, GPS, etc.)
- [ ] Store raw data in Parquet files organized by activity
- [ ] Determine data access patterns, data model, etc.
- [ ] Build incremental update script for new activities
- [ ] Identify and tag the 50+ attempts at primary climbing segment

#### Phase 1b: Live Sensor Data Ingestion (Future)
- [ ] Connect to BLE heart rate monitor and power meter
- [ ] Capture raw sensor streams with timestamps
- [ ] Use Flink to align/zip multi-rate sensor streams
- [ ] Write live data to same Parquet format as historical data
- [ ] Handle out-of-order data and sensor dropouts

### Phase 1.5: Data Exploration & Visualization
- [ ] Create Jupyter notebook for exploratory analysis
- [ ] Visualize HR/Power relationships across segment attempts
- [ ] Plot performance distribution (13-18 min range on climbing segment)
- [ ] Identify outlier attempts and examine context
- [ ] Generate summary statistics by effort type

### Phase 2: Batch Analysis (Spark)
- [ ] Extract all threshold efforts from historical data (>85% FTP, 5+ min)
- [ ] Build baseline HR/Power relationship model
- [ ] Analyze 50 climbing segment attempts:
  - [ ] Compare top 10 vs bottom 10 performances
  - [ ] Identify pacing patterns (steady vs variable power)
  - [ ] Examine HR response curves
  - [ ] Detect early indicators of strong/weak attempts
- [ ] Analyze 6 FTP tests for validation
- [ ] Document patterns that differentiate successful efforts

### Phase 2.5: Dashboard & Insights Visualization
- [ ] Build dashboard to display Phase 2 findings
- [ ] Visualize baseline models and performance patterns
- [ ] Create comparison views for segment attempts
- [ ] Display fatigue indicators and thresholds

### Phase 3: Real-Time Stream Processing (Flink)
- [ ] Set up Flink for real-time data processing
- [ ] Implement sliding window calculations (30s power, HR trends)
- [ ] Build fatigue state estimator using Phase 2 patterns
- [ ] Create real-time comparison to historical baselines
- [ ] Test with FTP test scenarios (20-min efforts in non-ERG mode)
- [ ] Generate real-time pacing guidance:
  - [ ] HR/Power decoupling metrics
  - [ ] Time-in-zone tracking
  - [ ] Comparison to successful historical attempts
  - [ ] Warning signals for degradation

### Phase 4: Future Enhancements
- [ ] Expand to other workout types beyond FTP tests
- [ ] Incorporate additional context (sleep, nutrition, training load)
- [ ] Build predictive models as more data accumulates
- [ ] Add audio/visual feedback for live workouts

## Data Sources
- **Primary**: 15-min climbing segment (~50 attempts, 13-18 min range)
- **Secondary**: 6 FTP tests (~20 min each)
- **Supporting**: All threshold efforts from ride history

## Technical Stack
- **Storage**: Parquet files + DuckDB for queries
- **Batch Processing**: Apache Spark
- **Stream Processing**: Apache Flink
- **Data Source**: Strava API (historical), BLE sensors (future live data)
- **Visualization**: Jupyter notebooks, dashboard TBD

## Getting Started

### Installation

```bash
poetry install
```

### Authentication

1. Set your Strava OAuth client credentials:

```bash
export STRAVA_CLIENT_ID=<your_client_id>
export STRAVA_CLIENT_SECRET=<your_client_secret>
```

2. Start the OAuth authorization flow:

```bash
poetry run python scripts/cli.py auth-start
```

3. Visit the URL printed above, authorize the application, and copy the `code` from the redirect URL.

4. Exchange the code for access tokens:

```bash
poetry run python scripts/cli.py auth-exchange <code>
```

5. Copy the export commands from the output and run them to set your tokens:

```bash
export STRAVA_ACCESS_TOKEN=<your_access_token>
export STRAVA_REFRESH_TOKEN=<your_refresh_token>
export STRAVA_EXPIRES_AT=<timestamp>
```

Alternatively, add all variables to a `.env` file in the project root:

```
STRAVA_CLIENT_ID=<your_client_id>
STRAVA_CLIENT_SECRET=<your_client_secret>
STRAVA_ACCESS_TOKEN=<your_access_token>
STRAVA_REFRESH_TOKEN=<your_refresh_token>
STRAVA_EXPIRES_AT=<timestamp>
```

### Usage

Fetch a page of activities:

```bash
poetry run python scripts/cli.py fetch-activities --per-page 30 --page 1
```

Fetch streams for a single activity:

```bash
poetry run python scripts/cli.py fetch-stream 123456789
```

### Docker Deployment

For Docker deployment, set all environment variables as container environment variables or use Docker secrets:

```dockerfile
docker run -e STRAVA_CLIENT_ID=... \
  -e STRAVA_CLIENT_SECRET=... \
  -e STRAVA_ACCESS_TOKEN=... \
  -e STRAVA_REFRESH_TOKEN=... \
  -e STRAVA_EXPIRES_AT=... \
  slipstream
```

Or use an env file with docker-compose:

```yaml
services:
  slipstream:
    image: slipstream
    env_file:
      - .env
```

