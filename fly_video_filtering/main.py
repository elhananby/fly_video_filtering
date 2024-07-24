import cv2
import os
import csv
import argparse
import logging
from tqdm import tqdm
import toml
import pkg_resources

def detect_object_threshold(frame, min_area, threshold_value):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    _, binary = cv2.threshold(gray, threshold_value, 255, cv2.THRESH_BINARY)
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    for contour in contours:
        if cv2.contourArea(contour) > min_area:
            return True
    return False

def detect_object_background_subtraction(frame, fgbg, min_area):
    fgmask = fgbg.apply(frame)
    contours, _ = cv2.findContours(fgmask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    for contour in contours:
        if cv2.contourArea(contour) > min_area:
            return True
    return False

def process_video(video_path, start_frame, end_frame, frame_perc, detection_method, config):
    cap = cv2.VideoCapture(video_path)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    if end_frame > total_frames:
        end_frame = total_frames
    
    frames_to_check = end_frame - start_frame + 1
    detections = 0
    
    cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
    
    if detection_method == 'background_subtraction':
        fgbg = cv2.createBackgroundSubtractorMOG2(
            history=config['background_subtraction']['history'],
            varThreshold=config['background_subtraction']['var_threshold'],
            detectShadows=config['background_subtraction']['detect_shadows']
        )
    
    for _ in tqdm(range(frames_to_check), desc=f"Processing {os.path.basename(video_path)}"):
        ret, frame = cap.read()
        if not ret:
            break
        
        if detection_method == 'threshold':
            if detect_object_threshold(frame, config['threshold']['min_area'], config['threshold']['threshold_value']):
                detections += 1
        elif detection_method == 'background_subtraction':
            if detect_object_background_subtraction(frame, fgbg, config['background_subtraction']['min_area']):
                detections += 1
    
    cap.release()
    
    detection_percentage = (detections / frames_to_check) * 100
    return detection_percentage >= frame_perc

def main():
    parser = argparse.ArgumentParser(description="Filter fly videos based on object detection")
    parser.add_argument("folder", help="Folder containing videos")
    parser.add_argument("start_frame", type=int, help="Start frame for detection")
    parser.add_argument("end_frame", type=int, help="End frame for detection")
    parser.add_argument("frame_perc", type=float, help="Percentage of frames to detect object")
    parser.add_argument("--method", choices=['threshold', 'background_subtraction'], default='threshold', help="Detection method to use")
    parser.add_argument("--config", default='config.toml', help="Path to the configuration file")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO if not args.debug else logging.DEBUG)
    logger = logging.getLogger(__name__)
    
    # Look for config file in multiple locations
    config_locations = [
        args.config,  # User-specified location
        'config.toml',  # Current directory
        pkg_resources.resource_filename('fly_video_filtering', 'config/config.toml')  # Package directory
    ]
    
    config = None
    for loc in config_locations:
        try:
            with open(loc, 'r') as config_file:
                config = toml.load(config_file)
            logger.info(f"Using configuration file: {loc}")
            break
        except FileNotFoundError:
            continue
    
    if config is None:
        logger.error("No configuration file found. Please provide a valid config.toml file.")
        return

    output_file = os.path.join(args.folder, 'detected_videos.csv')
    
    with open(output_file, 'w', newline='') as csvfile:
        csv_writer = csv.writer(csvfile)
        csv_writer.writerow(['video_path'])
        
        video_files = [f for f in os.listdir(args.folder) if f.endswith(('.mp4', '.avi', '.mov'))]
        
        for video_file in tqdm(video_files, desc="Processing videos"):
            video_path = os.path.join(args.folder, video_file)
            logger.info(f"Processing video: {video_path}")
            
            if process_video(video_path, args.start_frame, args.end_frame, args.frame_perc, args.method, config):
                logger.info(f"Object detected in {video_path}")
                csv_writer.writerow([video_path])
            else:
                logger.info(f"Object not detected in {video_path}")

if __name__ == "__main__":
    main()