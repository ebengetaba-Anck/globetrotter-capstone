document.addEventListener("DOMContentLoaded", () => {


    const token = localStorage.getItem("token");


    if (!token) {

        window.location.href = "/";

        return;

    }


    try {


        const payload = JSON.parse(atob(token.split(".")[1]));


        const username = payload.sub;


        const usernameElement = document.getElementById("username");


        if (usernameElement) {

            usernameElement.textContent = username;

        }


    } catch (e) {


        localStorage.removeItem("token");

        window.location.href = "/";


    }



    const logoutBtn = document.getElementById("logoutBtn");


    if (logoutBtn) {


        logoutBtn.addEventListener("click", () => {


            localStorage.removeItem("token");


            window.location.href = "/";


        });


    }


});