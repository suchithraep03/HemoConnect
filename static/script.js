
document.addEventListener("DOMContentLoaded", function () {
    console.log("HemoConnect loaded successfully.");

    // Handle donor registration form submission
    const donorForm = document.getElementById("donorForm");

    if (donorForm) {
        donorForm.addEventListener("submit", function () {
            const submitButton = donorForm.querySelector(
                'button[type="submit"], input[type="submit"]'
            );

            if (submitButton) {
                submitButton.disabled = true;

                if (submitButton.tagName === "BUTTON") {
                    submitButton.textContent = "Registering...";
                } else {
                    submitButton.value = "Registering...";
                }
            }
        });
    }

    // Confirm before resetting a form
    const resetButtons = document.querySelectorAll(
        'button[type="reset"], input[type="reset"]'
    );

    resetButtons.forEach(function (button) {
        button.addEventListener("click", function (event) {
            const confirmed = confirm(
                "Are you sure you want to clear the form?"
            );

            if (!confirmed) {
                event.preventDefault();
            }
        });
    });
});

