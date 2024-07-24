from setuptools import setup, find_packages

setup(
    name="fly_video_filtering",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        "opencv-python",
        "numpy",
        "tqdm",
        "toml",
        "flask",
    ],
    package_data={
        "fly_video_filtering": ["config/*.toml", "web_annotation/templates/*", "web_annotation/static/js/*"],
    },
    entry_points={
        "console_scripts": [
            "fly_video_filter=fly_video_filtering.main:main",
        ],
    },
)