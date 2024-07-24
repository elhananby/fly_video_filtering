# Video Object Detection

This Python package processes a folder of videos to detect objects within specified frame ranges using OpenCV. It supports two detection methods: thresholding and background subtraction. The script outputs a CSV file listing videos where objects were detected in at least a specified percentage of frames.

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/elhananby/fly_video_filtering.git
   cd fly_video_filtering
   ```

2. Create and activate the Conda environment:
   ```
   conda env create -f environment.yml
   conda activate fly-video-filtering
   ```

3. Install the package:
   ```
   pip install -e .
   ```

## Usage

Run the object detection script with the following command:

```
detect_objects /path/to/video/folder start_frame end_frame frame_percentage --method [threshold|background_subtraction] --config path/to/config.toml
```

Arguments:
- `/path/to/video/folder`: Directory containing the videos to process
- `start_frame`: Frame number to start detection (integer)
- `end_frame`: Frame number to end detection (integer)
- `frame_percentage`: Minimum percentage of frames that must contain an object (float)
- `--method`: Detection method to use (choices: 'threshold' or 'background_subtraction', default: 'threshold')
- `--config`: Path to the configuration file (default: 'config.toml')

Example:
```
detect_objects /home/user/videos 10 100 50.0 --method background_subtraction --config my_config.toml
```

This will process all videos in `/home/user/videos`, checking frames 10-100 for objects using the background subtraction method. Videos with objects detected in at least 50% of these frames will be listed in the output CSV.

## Configuration

The `config.toml` file contains parameters for both detection methods. You can modify these values to adjust the sensitivity of the object detection:

```toml
[threshold]
min_area = 500
threshold_value = 127

[background_subtraction]
min_area = 500
history = 500
var_threshold = 16
detect_shadows = true
```

## Output

The script generates a CSV file named `detected_videos.csv` in the input folder, listing paths of videos meeting the detection criteria.

## Development

To run tests:
```
python -m unittest discover tests
```