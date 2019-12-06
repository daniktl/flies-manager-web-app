let ls_login = document.getElementsByClassName("login-option");

function switchLogin() {
    console.log("here");
    for (let i=0; i< ls_login.length; i++){
        console.log(ls_login[i].id);
        if (ls_login[i].classList.contains("active")) {
            ls_login[i].classList.remove("active");
        }else {
            ls_login[i].classList.add("active");
        }
    }
    let ls_child = document.getElementsByClassName("login-body");
    for (let i=0; i<ls_child.length; i++){
        if (ls_child[i].classList.contains("hidden")) {
            ls_child[i].classList.remove("hidden");
            // ls_child[i].style.height = "0";
        }else{
            ls_child[i].classList.add("hidden");
            // let h = ls_child[i].offsetHeight;
            // ls_child[i].style.height = h+"px";
        }
    }

}

for (let i=0; i< ls_login.length; i++){
    ls_login[i].addEventListener("click tap", switchLogin);
}