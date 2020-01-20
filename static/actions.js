let ls_login = document.getElementsByClassName("login-option");

function switchLogin() {
    let to_hide = null;
    let to_show = null;
    for (let i = 0; i < ls_login.length; i++) {
        console.log(ls_login[i].id);
        if (ls_login[i].classList.contains("active")) {
            ls_login[i].classList.remove("active");
        } else {
            ls_login[i].classList.add("active");
        }
    }

    let ls_child = document.getElementsByClassName("login-body");
    for (let i = 0; i < ls_child.length; i++) {
        if (ls_child[i].classList.contains("hidden")) {
            to_show = ls_child[i];
        } else {
            ls_child[i].classList.add("hidden");
            ls_child[i].style.height = "";
        }
    }
    setTimeout(function () {
        to_show.classList.remove("hidden");
        let h = to_show.offsetHeight;
        to_show.style.height = h.toString() + "px";
    }, 100, false)

}

for (let i = 0; i < ls_login.length; i++) {
    ls_login[i].addEventListener("click tap", switchLogin);
}

window.onload = function () {
    let search_ls = document.getElementsByClassName("search-field");
    for (let i = 0; i < search_ls.length; i++) {
        let field = search_ls[i];
        field.addEventListener('keyup',
            function (e) {
                // if (e.keyCode === 13){
                filterTable(field);
                // }
            }
        )
    }
    let copy_btn = document.getElementsByClassName("copy-button");
    for (let btn_i = 0; btn_i < copy_btn.length; btn_i++) {
        let btn = copy_btn[btn_i];
        btn.addEventListener("click",
            function (e) {
                CopyToClipboard(this);
            })
    }
};

function recountPrice(){
    let price_div = document.getElementById("price-int");
    let discount_select = document.getElementById('discounts');
    let current_discount_str = discount_select.options[discount_select.selectedIndex].getAttribute("data-placeholder");
    let price = parseInt(price_div.getAttribute("data-placeholder"));
    let current_discount = parseInt(current_discount_str);
    if (!current_discount){
        document.getElementById("basic-price").classList.remove("bitted");
        document.getElementById("new-price").classList.remove("show");
    }else {
        document.getElementById("basic-price").classList.add("bitted");
        document.getElementById("new-price").classList.add("show");
    }
    document.getElementById("new-price-int").innerHTML = (price - price * (current_discount / 100)).toString();
}

function  buttonCorrect() {
    let state = document.getElementById("agree").checked;
    document.getElementById("confirm_btn").disabled = !state;
}

function CopyToClipboard(btn) {
    let containerid = btn.getAttribute("data-placeholder");
    if (document.selection) {
        var range = document.body.createTextRange();
        range.moveToElementText(document.getElementById(containerid));
        range.select().createTextRange();
        document.execCommand("copy");
        document.selection.empty();
    } else if (window.getSelection) {
        var range = document.createRange();
        range.selectNode(document.getElementById(containerid));
        window.getSelection().addRange(range);
        document.execCommand("copy");
        window.getSelection().empty();
    }
    let copy_btn = document.getElementsByClassName("copy-button");

    for (let btn_i = 0; btn_i < copy_btn.length; btn_i++) {
        let btn_tmp = copy_btn[btn_i];
        btn_tmp.classList.remove("active");
    }

    let texts = document.getElementsByClassName("copy-area");
    for (let text_id = 0; text_id < texts.length; text_id++) {
        let text_div = texts[text_id];
        text_div.classList.remove("active");

    }

    document.getElementById(containerid).classList.add("active");

    btn.classList.add("active");
}

function filterTable(field) {
    let table = document.getElementById(field.getAttribute("data-target"));
    if (!table) {
        return 0;
    }
    let text = field.value.toLowerCase();
    let children = table.children;
    for (let i = 0; i < children.length; i++) {

        if (!children[i].children[0].textContent.toLowerCase().includes(text)) {
            children[i].style.display = 'none';
        } else {
            children[i].style.display = '';
        }
    }
}