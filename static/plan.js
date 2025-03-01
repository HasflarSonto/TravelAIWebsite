document.addEventListener("DOMContentLoaded", function () {
    const tripForm = document.getElementById("trip-form");
    const loadingMessage = document.getElementById("loading-message");

    tripForm.addEventListener("submit", function (event) {
        event.preventDefault(); // Prevent default form submission

        // Gather form data
        const tripData = {
            naturalLanguageInput: document.getElementById("naturalLanguageInput").value,
            budget: document.getElementById("budget").value,
            peopleCount: document.getElementById("peopleCount").value,
            startDate: document.getElementById("startDate").value,
            endDate: document.getElementById("endDate").value
        };

        // Show loading message
        loadingMessage.style.display = "block";

        // Send data to backend
        fetch("/api/trip", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(tripData)
        })
        .then(response => response.json())
        .then(data => {
            loadingMessage.style.display = "none"; // Hide loading message

            if (data.success) {
                window.location.href = "/itinerary"; // Redirect to itinerary page
            } else {
                alert("Error: " + data.error);
            }
        })
        .catch(error => {
            loadingMessage.style.display = "none"; // Hide loading message
            console.error("Error creating trip:", error);
            alert("An error occurred. Please try again.");
        });
    });
});
