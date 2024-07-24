let currentFrame = 0;
let totalFrames = 100;  // Default value for debug mode
let currentVideo = null;
let skeletonConfig = null;
let currentPointIndex = 0;
let annotations = {};

document.addEventListener('DOMContentLoaded', function() {
    const videoSelect = document.getElementById('videoSelect');
    const frameSlider = document.getElementById('frameSlider');
    const frameInput = document.getElementById('frameInput');
    const prevFrameBtn = document.getElementById('prevFrame');
    const nextFrameBtn = document.getElementById('nextFrame');
    const videoFrame = document.getElementById('videoFrame');
    const annotationCanvas = document.getElementById('annotationCanvas');
    const ctx = annotationCanvas.getContext('2d');

    videoSelect.addEventListener('change', loadVideo);
    frameSlider.addEventListener('input', updateFrame);
    frameInput.addEventListener('change', updateFrame);
    prevFrameBtn.addEventListener('click', () => changeFrame(-1));
    nextFrameBtn.addEventListener('click', () => changeFrame(1));
    annotationCanvas.addEventListener('click', annotatePoint);

    fetchSkeletonConfig();

    function loadVideo() {
        currentVideo = videoSelect.value;
        fetch('/load_video', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({video_path: currentVideo})
        })
        .then(response => response.json())
        .then(data => {
            totalFrames = data.total_frames || 100;  // Use 100 frames if not specified (for debug mode)
            frameSlider.max = totalFrames - 1;
            frameInput.max = totalFrames - 1;
            currentFrame = 0;
            updateFrame();
            fetchAnnotations();
        });
    }

    function updateFrame() {
        currentFrame = parseInt(frameSlider.value);
        frameInput.value = currentFrame;
        fetch(`/get_frame?frame=${currentFrame}`)
        .then(response => response.blob())
        .then(blob => {
            const url = URL.createObjectURL(blob);
            videoFrame.src = url;
            videoFrame.onload = () => {
                annotationCanvas.width = videoFrame.width;
                annotationCanvas.height = videoFrame.height;
                drawAnnotations();
            };
        });
    }

    function changeFrame(delta) {
        currentFrame = Math.max(0, Math.min(totalFrames - 1, currentFrame + delta));
        frameSlider.value = currentFrame;
        updateFrame();
    }

    function annotatePoint(event) {
        const rect = annotationCanvas.getBoundingClientRect();
        const x = event.clientX - rect.left;
        const y = event.clientY - rect.top;
        const pointName = skeletonConfig.fly.points[currentPointIndex].name;
        
        if (!annotations[currentFrame]) {
            annotations[currentFrame] = [];
        }
        annotations[currentFrame].push([pointName, x, y]);
        
        currentPointIndex = (currentPointIndex + 1) % skeletonConfig.fly.points.length;
        
        drawAnnotations();
        saveAnnotation();
    }

    function drawAnnotations() {
        ctx.clearRect(0, 0, annotationCanvas.width, annotationCanvas.height);
        if (annotations[currentFrame]) {
            annotations[currentFrame].forEach(point => {
                const [name, x, y] = point;
                const color = skeletonConfig.fly.points.find(p => p.name === name).color;
                ctx.fillStyle = color;
                ctx.beginPath();
                ctx.arc(x, y, 5, 0, 2 * Math.PI);
                ctx.fill();
            });
        }
    }

    function saveAnnotation() {
        fetch('/save_annotation', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                frame: currentFrame,
                points: annotations[currentFrame]
            })
        });
    }

    function fetchAnnotations() {
        fetch('/get_annotations')
        .then(response => response.json())
        .then(data => {
            annotations = data;
            drawAnnotations();
        });
    }

    function fetchSkeletonConfig() {
        fetch('/get_skeleton_config')
        .then(response => response.json())
        .then(data => {
            skeletonConfig = data;
        });
    }
});