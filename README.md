# Fly Video Filtering and Annotation Tool

This project provides tools for filtering fly videos based on object detection and annotating the filtered videos. It consists of two main components:

1. A video filtering tool that processes videos to detect fly movement
2. An annotation tool with a graphical user interface for marking specific points on flies in the filtered videos

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/fly_video_filtering.git
   cd fly_video_filtering
   ```

2. Create and activate the Conda environment:
   ```
   conda env create -f environment.yml
   conda activate fly-video-filtering
   ```

3. Install the package in editable mode:
   ```
   pip install -e .
   ```

## Usage

### Video Filtering

To filter videos based on fly movement:

```
fly_video_filter /path/to/videos start_frame end_frame detection_percentage [--method {threshold|background_subtraction}] [--config path/to/config.toml]
```

Arguments:
- `/path/to/videos`: Directory containing the videos to process
- `start_frame`: Frame number to start detection (integer)
- `end_frame`: Frame number to end detection (integer)
- `detection_percentage`: Minimum percentage of frames that must contain detected movement (float)

Options:
- `--method`: Detection method to use (choices: 'threshold' or 'background_subtraction', default: 'threshold')
- `--config`: Path to a custom configuration file (default: package's config.toml)

Example:
```
fly_video_filter /home/user/fly_videos 500 650 90.0 --method background_subtraction
```

This command will process all videos in `/home/user/fly_videos`, checking frames 500-650 for fly movement using the background subtraction method. Videos with movement detected in at least 90% of these frames will be listed in the output CSV.

### Video Annotation

To run the annotation tool:

```
fly_video_annotate
```

This will open a file dialog to select:
1. The skeleton configuration file (skeleton.toml)
2. The CSV file containing the list of filtered videos

The GUI will then allow you to:
- Select videos from the list
- Navigate through video frames
- Annotate specific points on the fly (as defined in the skeleton.toml)
- Save annotations automatically

## Configuration

### Video Filtering Configuration (config.toml)

The `config.toml` file in the `fly_video_filtering/config/` directory contains parameters for both detection methods. You can modify these values to adjust the sensitivity of the object detection.

### Annotation Configuration (skeleton.toml)

The `skeleton.toml` file defines the points to be annotated on each fly. Modify this file to change the number or names of annotation points.

## Development

To run tests:
```
python -m unittest discover tests
```
