// const video = document.getElementById('video-stream');
// const originalButton = document.getElementById('original');
// const grayscaleButton = document.getElementById('grayscale');
// const blurButton = document.getElementById('blur');
// const captureButton = document.getElementById('capture');
// const capturedImage = document.getElementById('captured-image');

// originalButton.addEventListener('click', function () {
// 	video.src = "{{ url_for('video_feed') }}";
// });

// grayscaleButton.addEventListener('click', function () {
// 	video.src = "{{ url_for('video_feed') }}?filter=grayscale";
// });

// blurButton.addEventListener('click', function () {
// 	video.src = "{{ url_for('video_feed') }}?filter=blur";
// });

// captureButton.addEventListener('click', function () {
// 	fetch('/capture_image', {
// 		method: 'POST',
// 	})
// 		.then((response) => {
// 			if (response.ok) {
// 				return response.json(); // Suponiendo que la respuesta es un JSON con la URL
// 			} else {
// 				throw new Error('Error al capturar la imagen');
// 			}
// 		})
// 		.then((data) => {
// 			// Asumiendo que data contiene la URL de la imagen
// 			const imageUrl = data.images.large;
// 			capturedImage.src = imageUrl;
// 		})
// 		.catch((error) => {
// 			console.error(error);
// 		});
// });
