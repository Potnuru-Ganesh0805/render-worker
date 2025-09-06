document.addEventListener('DOMContentLoaded', () => {
    const imageInput = document.getElementById('imageInput');
    const imagePreview = document.getElementById('imagePreview');
    const detectButton = document.getElementById('detectButton');
    const webhookUrlInput = document.getElementById('webhookUrlInput'); // Get the new input element
    const resultDiv = document.getElementById('result');

    imageInput.addEventListener('change', function(event) {
        const file = event.target.files[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = function(e) {
                imagePreview.src = e.target.result;
                imagePreview.style.display = 'block';
                detectButton.style.display = 'block';
                resultDiv.textContent = '';
            };
            reader.readAsDataURL(file);
        }
    });

    detectButton.addEventListener('click', async () => {
        resultDiv.textContent = 'Processing... Please wait.';
        
        const apiEndpoint = 'https://luminous-backend-nc5e.onrender.com/predict';
        
        const webhookUrl = webhookUrlInput.value; // Get the URL from the input field
        const file = imageInput.files[0];

        if (!webhookUrl || !file) {
            resultDiv.textContent = 'Please provide both an image and a webhook URL.';
            return;
        }

        const formData = new FormData();
        formData.append('file', file);
        formData.append('webhook_url', webhookUrl); // Send the URL with the request

        try {
            const response = await fetch(apiEndpoint, {
                method: 'POST',
                body: formData
            });

            if (response.ok) {
                const data = await response.json();
                resultDiv.textContent = `Success! Your request has been queued.`;
            } else {
                resultDiv.textContent = 'Failed to submit the job.';
            }

        } catch (error) {
            console.error('Error:', error);
            resultDiv.textContent = 'An error occurred. Please try again.';
        }
    });
});
