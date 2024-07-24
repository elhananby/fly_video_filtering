import sys
import os
from typing import List, Dict, Tuple
import cv2
import toml
import argparse
from PySide6.QtWidgets import (
    QMainWindow,
    QFileDialog,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QListWidget,
    QLabel,
    QSlider,
    QLineEdit,
    QComboBox,
    QCheckBox,
    QApplication,
)
from PySide6.QtGui import (
    QImage,
    QPixmap,
    QPainter,
    QPen,
    QColor,
    QGuiApplication,
)
from PySide6.QtCore import Qt, QPoint

from fly_video_filtering.utils.annotation import save_annotations, load_annotations

# Predefined colors for automatic assignment
AUTO_COLORS = [
    "red",
    "green",
    "blue",
    "cyan",
    "magenta",
    "yellow",
    "black",
    "white",
    "darkRed",
    "darkGreen",
    "darkBlue",
    "darkCyan",
    "darkMagenta",
    "darkYellow",
]


class AnnotationGUI(QMainWindow):
    def __init__(self, video_list: List[str], skeleton_config: Dict):
        super().__init__()
        self.video_list = video_list
        self.skeleton_config = skeleton_config
        self.current_video = None
        self.cap = None
        self.current_frame = 0
        self.total_frames = 0
        self.annotations = {}
        self.auto_advance = False

        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Fly Video Annotation")
        self.setFixedSize(1000, 700)  # Fixed window size

        main_widget = QWidget()
        main_layout = QHBoxLayout()

        # Left panel
        left_panel = QWidget()
        left_layout = QVBoxLayout()
        self.video_list_widget = QListWidget()
        self.video_list_widget.addItems(self.video_list)
        self.video_list_widget.itemClicked.connect(self.load_video)
        left_layout.addWidget(QLabel("Videos:"))
        left_layout.addWidget(self.video_list_widget)

        # Point selection
        self.point_combo = QComboBox()
        self.point_combo.addItems(
            [
                f"{point['name']} ({point['color']})"
                for point in self.skeleton_config["fly"]["points"]
            ]
        )
        left_layout.addWidget(QLabel("Select point to annotate:"))
        left_layout.addWidget(self.point_combo)

        # Auto-advance checkbox
        self.auto_advance_checkbox = QCheckBox("Auto-advance to next point")
        self.auto_advance_checkbox.stateChanged.connect(self.toggle_auto_advance)
        left_layout.addWidget(self.auto_advance_checkbox)

        left_panel.setLayout(left_layout)

        # Right panel
        right_panel = QWidget()
        right_layout = QVBoxLayout()

        # Video display
        self.video_label = QLabel()
        self.video_label.setFixedSize(800, 600)  # Fixed video size
        self.video_label.mousePressEvent = self.annotate_point
        right_layout.addWidget(self.video_label)

        # Frame navigation
        nav_layout = QHBoxLayout()
        self.frame_slider = QSlider(Qt.Horizontal)
        self.frame_slider.valueChanged.connect(self.update_frame)
        nav_layout.addWidget(self.frame_slider)
        self.frame_input = QLineEdit()
        self.frame_input.setFixedWidth(50)
        self.frame_input.returnPressed.connect(self.jump_to_frame)
        nav_layout.addWidget(self.frame_input)
        right_layout.addLayout(nav_layout)

        right_panel.setLayout(right_layout)

        main_layout.addWidget(left_panel)
        main_layout.addWidget(right_panel)

        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

    def load_video(self, item):
        if self.current_video:
            self.save_current_annotations()

        self.current_video = item.text()
        self.cap = cv2.VideoCapture(self.current_video)
        self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.frame_slider.setRange(0, self.total_frames - 1)
        self.current_frame = 0
        self.frame_slider.setValue(0)
        self.annotations = {}
        self.load_existing_annotations()
        self.update_frame()

    def update_frame(self):
        if not self.cap:
            return

        self.current_frame = self.frame_slider.value()
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, self.current_frame)
        ret, frame = self.cap.read()
        if ret:
            self.display_frame(frame)
        self.frame_input.setText(str(self.current_frame))

    def display_frame(self, frame):
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame_rgb = cv2.resize(frame_rgb, (800, 600))  # Resize to 800x600
        h, w, ch = frame_rgb.shape
        bytes_per_line = ch * w
        image = QImage(frame_rgb.data, w, h, bytes_per_line, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(image)

        painter = QPainter(pixmap)
        for point in self.annotations.get(self.current_frame, []):
            point_name, x, y = point
            color = self.get_point_color(point_name)
            pen = QPen(color)
            pen.setWidth(3)
            painter.setPen(pen)
            painter.drawEllipse(QPoint(x, y), 5, 5)
        painter.end()

        self.video_label.setPixmap(pixmap)

    def annotate_point(self, event):
        if not self.cap:
            return

        pos = event.position()
        x = int(pos.x())
        y = int(pos.y())

        if self.current_frame not in self.annotations:
            self.annotations[self.current_frame] = []

        point_name = self.point_combo.currentText().split(" (")[0]

        # Remove existing annotation for this point (if any)
        self.annotations[self.current_frame] = [
            p for p in self.annotations[self.current_frame] if p[0] != point_name
        ]

        # Add new annotation
        self.annotations[self.current_frame].append((point_name, x, y))

        self.update_frame()
        self.save_current_annotations()

        # Auto-advance to next point if enabled
        if self.auto_advance:
            next_index = (
                self.point_combo.currentIndex() + 1
            ) % self.point_combo.count()
            self.point_combo.setCurrentIndex(next_index)

    def get_point_color(self, point_name):
        for point in self.skeleton_config["fly"]["points"]:
            if point["name"] == point_name:
                return QColor(point["color"])
        return QColor(Qt.red)  # Default color if not found

    def toggle_auto_advance(self, state):
        self.auto_advance = state == Qt.Checked

    def jump_to_frame(self):
        try:
            frame = int(self.frame_input.text())
            if 0 <= frame < self.total_frames:
                self.frame_slider.setValue(frame)
        except ValueError:
            pass

    def save_current_annotations(self):
        if self.current_video:
            save_annotations(self.current_video, self.annotations)

    def load_existing_annotations(self):
        base_name = os.path.splitext(os.path.basename(self.current_video))[0]
        csv_path = f"{base_name}_annotations.csv"
        if os.path.exists(csv_path):
            self.annotations = load_annotations(csv_path)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Left:
            self.frame_slider.setValue(max(0, self.current_frame - 1))
        elif event.key() == Qt.Key_Right:
            self.frame_slider.setValue(
                min(self.total_frames - 1, self.current_frame + 1)
            )
        # Add more shortcuts as needed


def run_gui(video_list: List[str], skeleton_config: Dict):
    app = QApplication(sys.argv)
    gui = AnnotationGUI(video_list, skeleton_config)
    gui.show()
    sys.exit(app.exec())


def main():
    # Create the QApplication instance first
    app = QApplication(sys.argv)

    parser = argparse.ArgumentParser(description="Fly Video Annotation Tool")
    parser.add_argument(
        "--config", help="Path to the skeleton configuration file (TOML)"
    )
    parser.add_argument("--video-list", help="Path to the video list file (CSV)")
    args = parser.parse_args()

    # Load skeleton configuration
    if args.config:
        if not os.path.exists(args.config):
            print(f"Error: Configuration file {args.config} not found.")
            sys.exit(1)
        skeleton_config_path = args.config
    else:
        skeleton_config_path = QFileDialog.getOpenFileName(
            None, "Select Skeleton Configuration File", "", "TOML Files (*.toml)"
        )[0]
        if not skeleton_config_path:
            print("No skeleton configuration file selected. Exiting.")
            sys.exit(1)

    with open(skeleton_config_path, "r") as skeleton_file:
        skeleton_config = toml.load(skeleton_file)

    # Load video list
    if args.video_list:
        if not os.path.exists(args.video_list):
            print(f"Error: Video list file {args.video_list} not found.")
            sys.exit(1)
        video_list_path = args.video_list
    else:
        video_list_path = QFileDialog.getOpenFileName(
            None, "Select Video List File", "", "CSV Files (*.csv)"
        )[0]
        if not video_list_path:
            print("No video list file selected. Exiting.")
            sys.exit(1)

    with open(video_list_path, "r") as f:
        video_list = [line.strip() for line in f]

    if not video_list:
        print("Error: No videos found in the video list file.")
        sys.exit(1)

    # Create and show the GUI
    gui = AnnotationGUI(video_list, skeleton_config)
    gui.show()

    # Start the event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
