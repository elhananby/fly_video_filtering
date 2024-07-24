import os
import cv2
import toml
from flask import Flask, render_template, request, jsonify, send_file
from fly_video_filtering.utils.annotation import save_annotations, load_annotations

app = Flask(__name__)

# Global variables
video_list = []
current_video = None
cap = None
total_frames = 0
skeleton_config = None


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


@app.route("/get_frame")
def get_frame():
    frame_number = int(request.args.get("frame", 0))
    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
    ret, frame = cap.read()
    if ret:
        _, buffer = cv2.imencode(".jpg", frame)
        return send_file(buffer.tobytes(), mimetype="image/jpeg")
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


def start_server(videos, config):
    global video_list, skeleton_config
    video_list = videos
    skeleton_config = config
    app.run(debug=True)


if __name__ == "__main__":
    # This is for testing purposes. In production, use the start_server function.
    video_list = ["/path/to/video1.mp4", "/path/to/video2.mp4"]
    with open("path/to/skeleton.toml", "r") as f:
        skeleton_config = toml.load(f)
    app.run(debug=True)
