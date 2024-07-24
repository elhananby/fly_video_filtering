import sys
import os
from typing import List, Dict, Tuple
import cv2
import toml
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                               QPushButton, QListWidget, QLabel, QSlider, QLineEdit, QFileDialog,
                               QMessageBox)
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
        left_layout.addWidget(self.video_list_widget)
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

        # Annotation controls
        annotation_layout = QHBoxLayout()
        self.current_point_label = QLabel("Current Point: ")
        annotation_layout.addWidget(self.current_point_label)
        self.remove_point_button = QPushButton("Remove Point")
        self.remove_point_button.clicked.connect(self.remove_current_point)
        annotation_layout.addWidget(self.remove_point_button)
        right_layout.addLayout(annotation_layout)

        right_panel.setLayout(right_layout)

        main_layout.addWidget(left_panel, 1)
        main_layout.addWidget(right_panel, 3)

        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

        self.video_label.mousePressEvent = self.annotate_point
        self.video_label.wheelEvent = self.zoom_image
        self.video_label.mouseMoveEvent = self.pan_image

    def load_video(self, item):
        if self.current_video:
            self.save_current_annotations()

        self.current_video = item.text()
        self.cap = cv2.VideoCapture(self.current_video)
        self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.frame_slider.setRange(0, self.total_frames - 1)
        self.current_frame = 0
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
        self.update_current_point_label()

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
        for point_name, x, y in self.annotations.get(self.current_frame, []):
            color = QColor(self.skeleton_config['fly']['points'][point_name]['color'])
            pen = QPen(color)
            pen.setWidth(3)
            painter.setPen(pen)
            painter.drawEllipse(QPoint(int(x * self.zoom_factor), int(y * self.zoom_factor)), 5, 5)
        painter.end()

        self.video_label.setPixmap(scaled_pixmap)

    def annotate_point(self, event):
        if not self.cap:
            return

        pos = event.pos()
        adjusted_x = (pos.x() - self.pan_offset.x()) / self.zoom_factor
        adjusted_y = (pos.y() - self.pan_offset.y()) / self.zoom_factor

        if self.current_frame not in self.annotations:
            self.annotations[self.current_frame] = []

        point_name = self.skeleton_config['fly']['points'][self.current_point_index]['name']
        self.annotations[self.current_frame].append((point_name, int(adjusted_x), int(adjusted_y)))
        self.current_point_index = (self.current_point_index + 1) % len(self.skeleton_config['fly']['points'])
        self.update_frame()
        self.save_current_annotations()

    def zoom_image(self, event):
        if event.angleDelta().y() > 0:
            self.zoom_factor *= 1.1
        else:
            self.zoom_factor /= 1.1
        self.zoom_factor = max(1.0, min(5.0, self.zoom_factor))  # Limit zoom between 1x and 5x
        self.update_frame()

    def pan_image(self, event):
        if event.buttons() == Qt.RightButton:
            self.pan_offset += event.pos() - self.last_pan_pos
            self.update_frame()
        self.last_pan_pos = event.pos()

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

    def update_current_point_label(self):
        if self.skeleton_config and 'fly' in self.skeleton_config and 'points' in self.skeleton_config['fly']:
            current_point = self.skeleton_config['fly']['points'][self.current_point_index]['name']
            self.current_point_label.setText(f"Current Point: {current_point}")

    def remove_current_point(self):
        if self.current_frame in self.annotations and self.annotations[self.current_frame]:
            self.annotations[self.current_frame].pop()
            self.update_frame()
            self.save_current_annotations()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Left:
            self.frame_slider.setValue(max(0, self.current_frame - 1))
        elif event.key() == Qt.Key_Right:
            self.frame_slider.setValue(min(self.total_frames - 1, self.current_frame + 1))
        elif event.key() == Qt.Key_1:
            self.current_point_index = 0
        elif event.key() == Qt.Key_2:
            self.current_point_index = 1
        # Add more shortcuts as needed
        self.update_current_point_label()

def run_annotation_gui():
    app = QApplication(sys.argv)
    
    # Load skeleton configuration
    skeleton_config_path = QFileDialog.getOpenFileName(None, "Select Skeleton Configuration File", "", "TOML Files (*.toml)")[0]
    if not skeleton_config_path:
        print("No skeleton configuration file selected. Exiting.")
        sys.exit(1)
    
    with open(skeleton_config_path, 'r') as skeleton_file:
        skeleton_config = toml.load(skeleton_file)
    
    # Load video list
    video_list_path = QFileDialog.getOpenFileName(None, "Select Video List File", "", "CSV Files (*.csv)")[0]
    if not video_list_path:
        print("No video list file selected. Exiting.")
        sys.exit(1)
    
    with open(video_list_path, 'r') as f:
        video_list = [line.strip() for line in f]
    
    gui = AnnotationGUI(video_list, skeleton_config)
    gui.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    run_annotation_gui()