import csv
import os
from typing import Dict, List, Tuple


def save_annotations(
    video_path: str, annotations: Dict[int, List[Tuple[str, int, int]]]
):
    """
    Save annotations to a CSV file.

    Args:
    video_path (str): Path to the video file
    annotations (Dict[int, List[Tuple[str, int, int]]]): Dictionary of frame annotations
        key: frame number
        value: list of tuples (point_name, x, y)
    """
    base_name = os.path.splitext(os.path.basename(video_path))[0]
    csv_path = f"{base_name}_annotations.csv"

    with open(csv_path, "w", newline="") as csvfile:
        fieldnames = ["frame", "point_name", "x", "y"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for frame, points in annotations.items():
            for point_name, x, y in points:
                writer.writerow(
                    {"frame": frame, "point_name": point_name, "x": x, "y": y}
                )


def load_annotations(csv_path: str) -> Dict[int, List[Tuple[str, int, int]]]:
    """
    Load annotations from a CSV file.

    Args:
    csv_path (str): Path to the CSV file containing annotations

    Returns:
    Dict[int, List[Tuple[str, int, int]]]: Dictionary of frame annotations
        key: frame number
        value: list of tuples (point_name, x, y)
    """
    annotations = {}
    if not os.path.exists(csv_path):
        return annotations

    with open(csv_path, "r") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            frame = int(row["frame"])
            point_name = row["point_name"]
            x, y = int(row["x"]), int(row["y"])
            if frame not in annotations:
                annotations[frame] = []
            annotations[frame].append((point_name, x, y))
    return annotations


def get_annotation_summary(
    annotations: Dict[int, List[Tuple[str, int, int]]],
) -> Dict[str, int]:
    """
    Generate a summary of the annotations.

    Args:
    annotations (Dict[int, List[Tuple[str, int, int]]]): Dictionary of frame annotations

    Returns:
    Dict[str, int]: Summary of annotations
        'total_frames': Total number of frames with annotations
        'total_points': Total number of points annotated
    """
    total_frames = len(annotations)
    total_points = sum(len(points) for points in annotations.values())
    return {"total_frames": total_frames, "total_points": total_points}


def validate_annotations(
    annotations: Dict[int, List[Tuple[str, int, int]]], expected_points: List[str]
) -> List[str]:
    """
    Validate the annotations against the expected points.

    Args:
    annotations (Dict[int, List[Tuple[str, int, int]]]): Dictionary of frame annotations
    expected_points (List[str]): List of expected point names

    Returns:
    List[str]: List of validation errors, if any
    """
    errors = []
    for frame, points in annotations.items():
        point_names = [p[0] for p in points]
        missing_points = set(expected_points) - set(point_names)
        extra_points = set(point_names) - set(expected_points)

        if missing_points:
            errors.append(f"Frame {frame}: Missing points: {', '.join(missing_points)}")
        if extra_points:
            errors.append(
                f"Frame {frame}: Unexpected points: {', '.join(extra_points)}"
            )

    return errors


def interpolate_missing_annotations(
    annotations: Dict[int, List[Tuple[str, int, int]]], total_frames: int
) -> Dict[int, List[Tuple[str, int, int]]]:
    """
    Interpolate missing annotations between keyframes.

    Args:
    annotations (Dict[int, List[Tuple[str, int, int]]]): Dictionary of frame annotations
    total_frames (int): Total number of frames in the video

    Returns:
    Dict[int, List[Tuple[str, int, int]]]: Dictionary of frame annotations with interpolated values
    """
    interpolated_annotations = annotations.copy()
    keyframes = sorted(annotations.keys())

    for i in range(len(keyframes) - 1):
        start_frame = keyframes[i]
        end_frame = keyframes[i + 1]

        for frame in range(start_frame + 1, end_frame):
            interpolated_annotations[frame] = []
            for start_point, end_point in zip(
                annotations[start_frame], annotations[end_frame]
            ):
                if start_point[0] != end_point[0]:
                    continue  # Skip if point names don't match

                t = (frame - start_frame) / (end_frame - start_frame)
                x = int(start_point[1] + t * (end_point[1] - start_point[1]))
                y = int(start_point[2] + t * (end_point[2] - start_point[2]))
                interpolated_annotations[frame].append((start_point[0], x, y))

    return interpolated_annotations


if __name__ == "__main__":
    # Example usage and testing
    test_annotations = {
        0: [("head", 100, 100), ("tail", 200, 200)],
        10: [("head", 110, 110), ("tail", 210, 210)],
    }

    # Test saving and loading
    save_annotations("test_video.mp4", test_annotations)
    loaded_annotations = load_annotations("test_video_annotations.csv")
    print("Loaded annotations:", loaded_annotations)

    # Test summary
    summary = get_annotation_summary(loaded_annotations)
    print("Annotation summary:", summary)

    # Test validation
    validation_errors = validate_annotations(loaded_annotations, ["head", "tail"])
    print("Validation errors:", validation_errors)

    # Test interpolation
    interpolated = interpolate_missing_annotations(loaded_annotations, 20)
    print("Interpolated annotations:", interpolated)
