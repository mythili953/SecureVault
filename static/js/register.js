let video = document.getElementById("video");
let canvas = document.getElementById("canvas");
let ctx = canvas.getContext("2d");
let stream = null;
let capturing = false;
let capturedImages = [];
let captureInterval = null;

async function startCamera() {
  try {
    stream = await navigator.mediaDevices.getUserMedia({
      video: { width: 640, height: 480 },
    });
    video.srcObject = stream;
    document.getElementById("captureBtn").disabled = false;
    document.getElementById("status").innerHTML =
      "Camera started. Position your face in the frame.";
  } catch (error) {
    console.log("Error accessing camera: " + error.message);
  }
}

function stopCamera() {
  if (stream) {
    stream.getTracks().forEach((track) => track.stop());
    video.srcObject = null;
    document.getElementById("captureBtn").disabled = true;
    document.getElementById("status").innerHTML = "Camera stopped.";
  }
}

function captureFrame() {
  ctx.drawImage(video, 0, 0, 640, 480);
  return canvas.toDataURL("image/jpeg", 0.8);
}

function startCapture() {
  const name = document.getElementById("nameInput").value.trim();
  if (!name) {
    alert("Please enter your name");
    return;
  }

  if (capturing) {
    alert("Capture already in progress");
    return;
  }

  if (!stream) {
    alert("Please start the camera first");
    return;
  }

  capturing = true;
  capturedImages = [];
  let count = 0;
  const totalImages = 50;

  document.getElementById("captureBtn").disabled = true;
  document.getElementById("status").innerHTML =
    "Capturing images... Keep your face visible!";

  captureInterval = setInterval(() => {
    if (count < totalImages) {
      const imageData = captureFrame();
      capturedImages.push(imageData);
      count++;

      const progress = (count / totalImages) * 100;
      document.getElementById("progressBar").style.width = progress + "%";
      document.getElementById(
        "status"
      ).innerHTML = `Capturing... ${count}/${totalImages} images`;
    } else {
      clearInterval(captureInterval);
      capturing = false;
      document.getElementById("captureBtn").disabled = false;
      document.getElementById("registerBtn").disabled = false;
      document.getElementById(
        "status"
      ).innerHTML = `Captured ${totalImages} images successfully!`;

      sendImagesToServer(name, capturedImages);
    }
  }, 200);
}

function sendImagesToServer(name, images) {
  document.getElementById("status").innerHTML = "Uploading images to server...";

  fetch("/upload_captured_images", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      name: name,
      images: images,
    }),
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.success) {
        document.getElementById("status").innerHTML = ` ${data.message}`;
      } else {
        document.getElementById("status").innerHTML = ` ${data.message}`;
      }
    })
    .catch((error) => {
      console.log(`Upload error: ${error}`);
    });
}

function registerFace() {
  const name = document.getElementById("nameInput").value.trim();
  if (!name) {
    alert("Please enter your name");
    return;
  }

  fetch("/register_face", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name: name }),
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.success) {
        document.getElementById("status").innerHTML = ` ${data.message}`;

        document.getElementById("nameInput").value = "";
        document.getElementById("progressBar").style.width = "0%";
        document.getElementById("registerBtn").disabled = true;
      } else {
        console.log(` ${data.message}`);
      }
    });
}

window.onload = function () {
  startCamera();
};

window.onbeforeunload = function () {
  stopCamera();
};
