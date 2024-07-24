from setuptools import setup, find_packages

setup(
    name="fly_video_filtering",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        "opencv-python",
        "tqdm",
        "toml",
        "PySide6",
    ],
    package_data={
        "fly_video_filtering": ["config/*.toml"],
    },
    entry_points={
        "console_scripts": [
            "fly_video_filter=fly_video_filtering.main:main",
            "fly_video_annotate=fly_video_filtering.annotation.gui:run_annotation_gui",
        ],
    },
)