from setuptools import setup, find_packages

setup(
    name="fly_video_filtering",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        "opencv-python",
        "tqdm",
    ],
    entry_points={
        "console_scripts": [
            "detect_objects=fly_video_filtering.main:main",
        ],
    },
)