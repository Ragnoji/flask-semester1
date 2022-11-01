import ImageTools from "./imageResizer";

let buttons = document.querySelectorAll('.buy');
let logout_button = document.querySelector('.logout');
let content = document.querySelector('.content');
let auth_window = document.querySelector('.auth-wrapper');
let count = $('.products-in-cart')[0];

buttons.forEach(button => {
    button.addEventListener('click', function (event) {
        // event.preventDefault();
        $.ajax({
            headers: { "X-CSRF-Token": getCookie("csrf_access_token") },
            url: '/cart_append',
            method: 'post'
        });
    });
});

logout_button.addEventListener('click', function (event) {
    event.preventDefault();
    $.ajax({
        headers: { "X-CSRF-Token": getCookie("csrf_access_token") },
        url: '/logout',
        method: 'post',
    });
    location.reload();
});

function createCookie(name, value, days) {
    let expires;
    if (days) {
        let date = new Date();
        date.setTime(date.getTime() + (days * 24 * 60 * 60 * 1000));
        expires = "; expires=" + date.toGMTString();
    }
    else {
        expires = "";
    }
    document.cookie = name + "=" + value + expires + "; path=/";
}

function getCookie(c_name) {
    if (document.cookie.length > 0) {
        let c_start = document.cookie.indexOf(c_name + "=");
        if (c_start != -1) {
            c_start = c_start + c_name.length + 1;
            let c_end = document.cookie.indexOf(";", c_start);
            if (c_end == -1) {
                c_end = document.cookie.length;
            }
            return unescape(document.cookie.substring(c_start, c_end));
        }
    }
    return "";
}

console.log(getCookie("csrf_refresh_token"));