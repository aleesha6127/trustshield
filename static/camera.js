const video = document.getElementById("video");
navigator.mediaDevices.getUserMedia({ video: true })
  .then(stream => video.srcObject = stream);

function capture() {
  const canvas = document.getElementById("canvas");
  canvas.width = video.videoWidth;
  canvas.height = video.videoHeight;
  canvas.getContext("2d").drawImage(video, 0, 0);
  document.getElementById("image").value =
    canvas.toDataURL("image/png");
}
