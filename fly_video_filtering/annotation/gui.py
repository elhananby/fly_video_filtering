import sys
import os
from typing import List, Dict, Tuple
import cv2
import toml
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                               QPushButton, QListWidget, QLabel, QSlider, QLineEdit, QFileDialog,
                               QMessageBox, QComboBox)
from PySide6.QtGui import QImage, QPixmap, QPainter, QPen, QColor
from PySide6.QtCore import Qt, QPoint

from fly_video_filtering.utils.annotation import save_annotations, load_annotations

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
        self.current_point_index = 0
        self.zoom_factor = 1.0
        self.pan_offset = QPoint(0, 0)

        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('Fly Video Annotation')
        self.setGeometry(100, 100, 1200, 800)

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
        self.point_combo.addItems([point['name'] for point in self.skeleton_config['fly']['points']])
        self.point_combo.currentIndexChanged.connect(self.update_current_point)
        left_layout.addWidget(QLabel("Select point to annotate:"))
        left_layout.addWidget(self.point_combo)

        left_panel.setLayout(left_layout)

        # Right panel
        right_panel = QWidget()
        right_layout = QVBoxLayout()

        # Video display
        self.video_label = QLabel()
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

        main_layout.addWidget(left_panel, 1)
        main_layout.addWidget(right_panel, 3)

        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

        self.video_label.mousePressEvent = self.annotate_point
        self.video_label.wheelEvent = self.zoom_image

    def load_video(self, item):
        if self.current_video:
            self.save_current_annotations()

        self.current_video = item.text()
        self.cap = cv2.VideoCapture(self.current_video)
        self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.frame_slider.setRange(0, self.total_frames - 1)
        self.current_frame = 0  # Reset to frame 0
        self.frame_slider.setValue(0)  # Reset slider to 0
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
        h, w, ch = frame_rgb.shape
        bytes_per_line = ch * w
        image = QImage(frame_rgb.data, w, h, bytes_per_line, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(image)

        # Apply zoom and pan
        scaled_pixmap = pixmap.scaled(pixmap.width() * self.zoom_factor, pixmap.height() * self.zoom_factor, 
                                      Qt.KeepAspectRatio, Qt.SmoothTransformation)
        
        painter = QPainter(scaled_pixmap)
        for point in self.annotations.get(self.current_frame, []):
            point_name, x, y = point
            color = self.get_point_color(point_name)
            pen = QPen(color)
            pen.setWidth(3)
            painter.setPen(pen)
            painter.drawEllipse(QPoint(int(x * self.zoom_factor), int(y * self.zoom_factor)), 5, 5)
        painter.end()

        self.video_label.setPixmap(scaled_pixmap)

    def get_point_color(self, point_name):
        for point in self.skeleton_config['fly']['points']:
            if point['name'] == point_name:
                return QColor(point['color'])
        return QColor(Qt.red)  # Default color if not found

    def annotate_point(self, event):
        if not self.cap:
            return

        pos = event.position()
        adjusted_x = (pos.x() - self.pan_offset.x()) / self.zoom_factor
        adjusted_y = (pos.y() - self.pan_offset.y()) / self.zoom_factor

        if self.current_frame not in self.annotations:
            self.annotations[self.current_frame] = []

        point_name = self.point_combo.currentText()
        
        # Remove existing annotation for this point (if any)
        self.annotations[self.current_frame] = [p for p in self.annotations[self.current_frame] if p[0] != point_name]
        
        # Add new annotation
        self.annotations[self.current_frame].append((point_name, int(adjusted_x), int(adjusted_y)))
        
        self.update_frame()
        self.save_current_annotations()

    def update_current_point(self, index):
        self.current_point_index = index

    def zoom_image(self, event):
        if event.angleDelta().y() > 0:
            self.zoom_factor *= 1.1
        else:
            self.zoom_factor /= 1.1
        self.update_frame()

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
            self.frame_slider.setValue(min(self.total_frames - 1, self.current_frame + 1))
        # Add more shortcuts as needed

def run_gui(video_list: List[str], skeleton_config: Dict):
    app = QApplication(sys.argv)
    gui = AnnotationGUI(video_list, skeleton_config)
    gui.show()
    sys.exit(app.exec())

def main():
    # Load skeleton configuration
    skeleton_config_path = QFileDialog.getOpenFileName(None, "Select Skeleton Configuration File", "", "TOML Files (*.toml)")[0]
    if not skeleton_config_path:
        print("No skeleton configuration file selected. Exiting.")
        sys.exit(1)
    
    with open(skeleton_config_path, 'r') as skeleton_file:
        skeleton_config = toml.load(skeleton_file)
    
    # Load video list
    video_list_path = QFileDialog.getOpenFileName(None, "Select Video List File", "", "CSV Files (*.csv)")[0]
    if not skeleton_config_path:
        print("No video list file selected. Exiting.")
        sys.exit(1)
    
    with open(video_list_path, 'r') as f:
        video_list = [line.strip() for line in f]
    
    run_gui(video_list, skeleton_config)

if __name__ == "__main__":
    main()