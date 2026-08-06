/* =====================================
   Ô'MBOA - LOGIN JAVASCRIPT
===================================== */


document.addEventListener("DOMContentLoaded", () => {



    // Afficher / cacher mot de passe

    const togglePassword = document.getElementById(
        "togglePassword"
    );


    const password = document.getElementById(
        "password"
    );



    if(togglePassword && password){


        togglePassword.addEventListener(
            "click",
            () => {


                if(password.type === "password"){


                    password.type = "text";


                    togglePassword.classList.remove(
                        "fa-eye"
                    );


                    togglePassword.classList.add(
                        "fa-eye-slash"
                    );


                }else{


                    password.type = "password";


                    togglePassword.classList.remove(
                        "fa-eye-slash"
                    );


                    togglePassword.classList.add(
                        "fa-eye"
                    );


                }


            }
        );


    }






    // Animation légère de la carte login


    const card = document.querySelector(
        ".login-card"
    );


    if(card){


        card.style.opacity = "0";


        card.style.transform =
        "translateY(20px)";



        setTimeout(()=>{


            card.style.transition =
            "all .6s ease";



            card.style.opacity = "1";


            card.style.transform =
            "translateY(0)";



        },100);


    }


const loginBtn = document.getElementById("loginBtn");


if(loginBtn){

    loginBtn.addEventListener("click", async ()=>{


        const username =
        document.getElementById("username").value;


        const password =
        document.getElementById("password").value;



        const response = await fetch("/login", {

            method:"POST",

            headers:{
                "Content-Type":"application/json"
            },

            body:JSON.stringify({

                username:username,

                password:password

            })

        });



        const data = await response.json();



       if(response.ok){


    localStorage.setItem(
        "token",
        data.token
    );


    alert("Connexion réussie");


    window.location.href="/dashboard";


}else{


    alert(data.error || "Erreur de connexion");


}


});


}


});