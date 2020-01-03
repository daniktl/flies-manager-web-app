let ls_login = document.getElementsByClassName("login-option");

function switchLogin() {
    let to_hide = null;
    let to_show = null;
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
            to_show = ls_child[i];
        }else{
            ls_child[i].classList.add("hidden");
            ls_child[i].style.height = "";
        }
    }
    setTimeout(function () {
        to_show.classList.remove("hidden");
    let h = to_show.offsetHeight;
    to_show.style.height = h.toString()+"px";
    }, 100, false)

}

for (let i=0; i< ls_login.length; i++){
    ls_login[i].addEventListener("click tap", switchLogin);
}

window.onload = function () {
    let search_ls = document.getElementsByClassName("search-field");
    for (let i = 0; i < search_ls.length; i++) {
        let field = search_ls[i];
        field.addEventListener('keyup',
            function (e){
                // if (e.keyCode === 13){
                    filterTable(field);
                // }
            }
        )

    }
};

function filterTable(field) {
    let table = document.getElementById(field.getAttribute("data-target"));
    if (!table){
        return 0;
    }
    let text = field.value.toLowerCase();
    let children = table.children;
    for (let i=0; i < children.length; i++){

        if (!children[i].children[0].textContent.toLowerCase().includes(text)){
            children[i].style.display = 'none';
        }else {
            children[i].style.display = '';
        }
    }
}