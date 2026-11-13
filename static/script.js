function sendSOS() {

    const status = document.getElementById("status");
    const messageBox = document.getElementById("message");
    const smsLinks = document.getElementById("smsLinks");

    status.innerText = "Getting your location...";
    messageBox.innerText = "";
    smsLinks.innerHTML = "";

    if (!navigator.geolocation) {
        status.innerText = "GPS location is not supported.";
        return;
    }

    navigator.geolocation.getCurrentPosition(
        function(position) {

            const latitude = position.coords.latitude;
            const longitude = position.coords.longitude;

            status.innerText = "Sending emergency alert...";

            fetch("/send_alert", {
                method: "POST",

                headers: {
                    "Content-Type": "application/json"
                },

                body: JSON.stringify({
                    latitude: latitude,
                    longitude: longitude
                })
            })

            .then(response => response.json())

            .then(data => {

                if (data.status === "success") {

                    status.innerText = "Alert saved successfully!";

                    messageBox.innerText = data.message;

                    const heading = document.createElement("h4");
                    heading.innerText = "Send SMS to trusted contacts:";
                    smsLinks.appendChild(heading);

                    trustedContacts.forEach(contact => {

                        const link = document.createElement("a");

                        link.href = "sms:" + contact.phone +
                            "?body=" + encodeURIComponent(data.message);

                        link.innerText = "Send SMS to " + contact.name;

                        link.className = "sms-link";

                        smsLinks.appendChild(link);
                    });

                } else {
                    status.innerText = data.error || "Alert failed.";
                }

            })

            .catch(error => {
                status.innerText = "Network error. Please try again.";
            });

        },

        function(error) {

            status.innerText =
                "Unable to get location. Please enable location permission.";

        },

        {
            enableHighAccuracy: true,
            timeout: 15000,
            maximumAge: 0
        }
    );
}