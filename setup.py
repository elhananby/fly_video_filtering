from setuptools import setup, find_packages

setup(
    name="fly_video_filtering",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        "opencv-python",
        "tqdm",
        "toml",
    ],
    package_data={
        "fly_video_filtering": ["config/config.toml"],
    },
    entry_points={
        "console_scripts": [
            "filter_fly_videos=fly_video_filtering.main:main",
        ],
    },
)