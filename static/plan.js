document.addEventListener("DOMContentLoaded", function () {
    const tripForm = document.getElementById("trip-form");
    const generateButton = document.querySelector(".btn");
    const loadingMessage = document.getElementById("loading-message");

    tripForm.addEventListener("submit", async function (event) {
        event.preventDefault();
        
        generateButton.disabled = true;
        generateButton.innerText = "Generating...";
        loadingMessage.style.display = "block";

        const formData = {
            startLocation: document.getElementById("startLocation").value,
            endLocation: document.getElementById("endLocation").value,
            naturalLanguageInput: document.getElementById("naturalLanguageInput").value,
            budget: document.getElementById("budget").value,
            peopleCount: document.getElementById("peopleCount").value,
            startDate: document.getElementById("startDate").value,
            endDate: document.getElementById("endDate").value
        };

        try {
            const response = await fetch('/api/trip', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(formData)
            });

            const data = await response.json();
            if (data.success) {
                window.location.href = '/suggestions';
            } else {
                throw new Error(data.error || 'Failed to generate itinerary');
            }
        } catch (error) {
            alert('Error: ' + error.message);
            generateButton.disabled = false;
            generateButton.innerText = "Generate Itinerary";
            loadingMessage.style.display = "none";
        }
    });
});
