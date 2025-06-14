let video = document.getElementById('video');
let canvas = document.getElementById('canvas');
let ctx = canvas.getContext('2d');
let stream = null;

async function startCamera() {
    try {
        stream = await navigator.mediaDevices.getUserMedia({ 
            video: { width: 640, height: 480 } 
        });
        video.srcObject = stream;
        document.getElementById('authBtn').disabled = false;
        document.getElementById('status').innerHTML = 'Camera started. Position your face in the frame.';
    } catch (error) {
        console.log( 'Error accessing camera: ' + error.message);
    }
}

function stopCamera() {
    if (stream) {
        stream.getTracks().forEach(track => track.stop());
        video.srcObject = null;
        document.getElementById('authBtn').disabled = true;
        document.getElementById('status').innerHTML = 'Camera stopped.';
    }
}

function captureFrame() {
    ctx.drawImage(video, 0, 0, 640, 480);
    return canvas.toDataURL('image/jpeg', 0.8);
}

function authenticateFace() {
    if (!stream) {
        alert('Please start the camera first');
        return;
    }

    document.getElementById('status').innerHTML = 'Authenticating...';
    
    const imageData = captureFrame();
    
    fetch('/authenticate_face', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({image: imageData})
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            document.getElementById('status').innerHTML = `<span class="success"> ${data.message}</span>`;

            setTimeout(() => {
                window.location.href = `/vault?user=${encodeURIComponent(data.user.name)}`;
            }, 1500);
        } else {
            document.getElementById('status').innerHTML = `<span class="error">${data.message}</span>`;
        }
    })
    .catch(error => {
      console.log(`<span class="error">Authentication error: ${error}</span>`);
    });
}

window.onload = function() {
    startCamera();
};

window.onbeforeunload = function() {
    stopCamera();
};
