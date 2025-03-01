document.addEventListener("DOMContentLoaded", function () {
    document.getElementById("trip-form").addEventListener("submit", function (event) {
        event.preventDefault(); // Prevent default form submission

        const generateButton = document.querySelector(".btn");
        const loadingMessage = document.getElementById("loading-message");

        // Show the loading message and disable the button
        generateButton.disabled = true;
        generateButton.innerText = "Generating...";
        loadingMessage.style.display = "block";

        const tripData = {
            startLocation: document.getElementById("startLocation").value.trim(),
            endLocation: document.getElementById("endLocation").value.trim(),
            naturalLanguageInput: document.getElementById("naturalLanguageInput").value.trim(),
            budget: document.getElementById("budget").value.trim(),
            peopleCount: document.getElementById("peopleCount").value.trim(),
            startDate: document.getElementById("startDate").value.trim(),
            endDate: document.getElementById("endDate").value.trim()
        };

        // Ensure all fields are included
        for (let field in tripData) {
            if (!tripData[field]) {
                alert(`Missing field: ${field}`);
                generateButton.disabled = false;
                generateButton.innerText = "Generate Itinerary";
                loadingMessage.style.display = "none";
                return;
            }
        }

        fetch("/api/trip", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(tripData)
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                window.location.href = "/itinerary";
            } else {
                alert("Error: " + data.error);
                generateButton.disabled = false;
                generateButton.innerText = "Generate Itinerary";
                loadingMessage.style.display = "none";
            }
        })
        .catch(error => {
            console.error("Error:", error);
            alert("An error occurred while generating your itinerary.");
            generateButton.disabled = false;
            generateButton.innerText = "Generate Itinerary";
            loadingMessage.style.display = "none";
        });
    });
});
