document.addEventListener('DOMContentLoaded', () => {
    const imageInput = document.getElementById('imageInput');
    const imagePreview = document.getElementById('imagePreview');
    const detectButton = document.getElementById('detectButton');
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
        
        // This is your deployed Render web service URL
        const apiEndpoint = 'https://YOUR_RENDER_SERVICE_URL.onrender.com/predict';

        // Use a temporary webhook URL to see the results.
        const webhookUrl = 'https://your-webhook-test-url.com/receive'; 
        
        const imageUrl = imagePreview.src;

        try {
            const response = await fetch(apiEndpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    image_url: imageUrl,
                    webhook_url: webhookUrl
                })
            });

            if (response.ok) {
                const data = await response.json();
                resultDiv.textContent = `Success! Your request has been queued.`;
                // The actual results will be sent to your webhook URL
            } else {
                resultDiv.textContent = 'Failed to submit the job.';
            }

        } catch (error) {
            console.error('Error:', error);
            resultDiv.textContent = 'An error occurred. Please try again.';
        }
    });
});
