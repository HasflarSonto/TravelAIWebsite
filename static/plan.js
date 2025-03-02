document.addEventListener("DOMContentLoaded", function () {
    const tripForm = document.getElementById("trip-form");
    const generateButton = document.querySelector(".btn");
    const loadingAnimation = document.querySelector(".loading-animation");

    tripForm.addEventListener("submit", async function (event) {
        event.preventDefault();
        
        generateButton.disabled = true;
        loadingAnimation.style.display = "flex";

        try {
            // First save the trip parameters
            const response = await fetch('/api/trip/generate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    startLocation: document.getElementById("startLocation").value.trim(),
                    endLocation: document.getElementById("endLocation").value.trim(),
                    naturalLanguageInput: document.getElementById("naturalLanguageInput").value.trim(),
                    budget: document.getElementById("budget").value,
                    peopleCount: document.getElementById("peopleCount").value,
                    startDate: document.getElementById("startDate").value,
                    endDate: document.getElementById("endDate").value
                })
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
            }

            // If successful, redirect to suggestions page
            window.location.href = '/suggestions';
            
        } catch (error) {
            console.error('Error:', error);
            if (error.message === 'Failed to fetch') {
                alert('Unable to connect to the server. Please check your internet connection and try again.');
            } else {
                alert('Error: ' + error.message);
            }
        } finally {
            generateButton.disabled = false;
            loadingAnimation.style.display = "none";
        }
    });
});
