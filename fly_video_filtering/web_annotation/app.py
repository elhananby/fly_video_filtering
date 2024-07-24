import os
import cv2
import toml
import argparse
from flask import Flask, render_template, request, jsonify, send_file
from fly_video_filtering.utils.annotation import save_annotations, load_annotations
import numpy as np

app = Flask(__name__)

# Global variables
video_list = []
current_video = None
cap = None
total_frames = 0
skeleton_config = None
debug_mode = False

@app.route("/")
def index():
    return render_template("index.html", videos=video_list)


@app.route("/load_video", methods=["POST"])
def load_video():
    global current_video, cap, total_frames
    video_path = request.json["video_path"]
    current_video = video_path
    cap = cv2.VideoCapture(video_path)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    return jsonify({"total_frames": total_frames})


@app.route('/get_frame')
def get_frame():
    frame_number = int(request.args.get('frame', 0))
    if debug_mode:
        # Generate a sample frame for debug mode
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        cv2.putText(frame, f"Debug Frame {frame_number}", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        _, buffer = cv2.imencode('.jpg', frame)
        return send_file(buffer.tobytes(), mimetype='image/jpeg')
    else:
        # Existing code for real video frames
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
        ret, frame = cap.read()
        if ret:
            _, buffer = cv2.imencode('.jpg', frame)
            return send_file(buffer.tobytes(), mimetype='image/jpeg')
        return "Frame not found", 404



@app.route("/save_annotation", methods=["POST"])
def save_annotation():
    data = request.json
    frame = data["frame"]
    points = data["points"]
    annotations = load_annotations(current_video + "_annotations.csv")
    annotations[frame] = points
    save_annotations(current_video, annotations)
    return "Annotation saved", 200


@app.route("/get_annotations")
def get_annotations():
    annotations = load_annotations(current_video + "_annotations.csv")
    return jsonify(annotations)


@app.route("/get_skeleton_config")
def get_skeleton_config():
    return jsonify(skeleton_config)

def start_server(videos, config, host, port):
    global video_list, skeleton_config
    video_list = videos
    skeleton_config = config
    app.run(host=host, port=port, debug=True)

def main():
    parser = argparse.ArgumentParser(description="Start the fly video annotation server")
    parser.add_argument("video_list_file", nargs='?', help="Path to the CSV file containing the list of videos")
    parser.add_argument("--skeleton", default=os.path.join(os.path.dirname(__file__), '..', 'config', 'skeleton.toml'), help="Path to the skeleton configuration file")
    parser.add_argument("--host", default="127.0.0.1", help="Host to run the server on")
    parser.add_argument("--port", type=int, default=5000, help="Port to run the server on")
    parser.add_argument("--debug", action="store_true", help="Run in debug mode with sample data")
    args = parser.parse_args()

    global debug_mode
    debug_mode = args.debug

    if debug_mode:
        print("Running in debug mode with sample data")
        skeleton_config = {
            "fly": {
                "points": [
                    {"name": "head", "color": "#FF0000"},
                    {"name": "thorax", "color": "#00FF00"},
                    {"name": "abdomen", "color": "#0000FF"}
                ]
            }
        }
        video_list = ["sample_video_1.mp4", "sample_video_2.mp4"]
    else:
        if not args.video_list_file:
            print("Error: video_list_file is required when not in debug mode")
            return

        with open(args.skeleton, 'r') as skeleton_file:
            skeleton_config = toml.load(skeleton_file)
        
        with open(args.video_list_file, 'r') as f:
            video_list = [line.strip() for line in f]

    print(f"Starting annotation server on {args.host}:{args.port}")
    print(f"Loaded {len(video_list)} videos and skeleton configuration")
    
    start_server(video_list, skeleton_config, args.host, args.port)

if __name__ == '__main__':
    main()