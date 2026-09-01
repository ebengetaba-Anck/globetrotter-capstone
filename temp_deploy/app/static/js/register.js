document.addEventListener("DOMContentLoaded", () => {

    const registerBtn = document.getElementById("registerBtn");

    registerBtn.addEventListener("click", async () => {

        const username = document.getElementById("username").value.trim();
        const email = document.getElementById("email").value.trim();
        const phone = document.getElementById("phone").value.trim();
        const password = document.getElementById("password").value;
        const confirmPassword = document.getElementById("confirmPassword").value;

        if (!username || !email || !password) {
            alert("Veuillez remplir tous les champs obligatoires.");
            return;
        }

        if (password !== confirmPassword) {
            alert("Les mots de passe ne correspondent pas.");
            return;
        }

        try {

            const response = await fetch("/register", {

                method: "POST",

                headers: {
                    "Content-Type": "application/json"
                },

                body: JSON.stringify({
                    username: username,
                    password: password,
                    email: email,
                    phone: phone,
                    preferences: []
                })

            });

            const data = await response.json();

            if (response.ok) {

                alert("Compte créé avec succès !");

                window.location.href = "/";

            } else {

                alert(data.error || "Une erreur est survenue.");

            }

        } catch (error) {

            console.error(error);

            alert("Impossible de contacter le serveur.");

        }

    });

});