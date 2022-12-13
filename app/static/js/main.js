let signin_window = document.querySelector('#signinModal');
let signup_window = document.querySelector('#signupModal');
let content = document.querySelector('.content');

$(document).ready(function(){
   bindProduct();
   bindWish();
   bindPaginationClick();
});

function bindProduct() {
    $('button.buy').on('click', function () {
        let btn = this;
        if (btn.hasAttribute("data-redirect")) {
            window.location.replace(btn.getAttribute('data-redirect'));
            return
        }
        btn.disabled = true;
        $.ajax({
            headers: {"X-CSRF-Token": getCookie("csrf_access_token")},
            url: '/cart/append',
            method: 'post',
            data: JSON.stringify({id: parseInt(btn.getAttribute('data-product_id'), 10)}),
            contentType: "application/json",
            success: function (data) {
                if (data['success'] === 1) {
                    btn.disabled = false;
                    btn.innerText = "В корзине";
                    btn.classList.add("button-done");
                    btn.setAttribute("data-redirect", "/cart/");
                    let label = $('span.cart-label')
                    label.addClass('cart-cost')
                    label.text(data['cost']);
                    $('.products-in-cart').text(data['qty']);

                } else {
                    btn.innerText = "Ошибка";
                    setTimeout(function () {
                        btn.disabled = false;
                        btn.innerText = "В корзину";
                    }, 2000);
                }
            },
            error: function (data) {
                btn.innerText = "Ошибка";
                setTimeout(function () {
                    btn.disabled = false;
                    btn.innerText = "В корзину";
                }, 2000);
            }
        });
    });

    let product_div = $('div.product');

    product_div.mouseenter(function (event) {
        let target = event.target;
        let button = $(target).find('button.buy');
        button.removeClass('button-ui_passive');
    });

    product_div.mouseleave(function (event) {
        let target = event.target;
        let button = $(target).find('button.buy');
        button.addClass('button-ui_passive');
    });
}

function bindWish() {
    $('button.wishlist-btn:not(.cart)').on('click', function () {
        let btn = this;
        btn.disabled = true;
        let type = btn.classList.contains('button-done')
        let endpoint = type ? '/remove_favorite' : '/add_favorite'
        $.ajax({
            headers: {"X-CSRF-Token": getCookie("csrf_access_token")},
            url: endpoint,
            method: 'post',
            data: JSON.stringify({id: parseInt(btn.getAttribute('data-product_id'), 10)}),
            contentType: "application/json",
            success: function (data) {
                if (data['success'] === 1) {
                    if (type) {
                        btn.classList.remove("button-done");
                        let wish_count = $('.to-wish > div.products-in-wish');
                        prev_count = parseInt(wish_count.text());
                        wish_count.text(prev_count - 1);
                    } else {
                        btn.classList.add("button-done");
                        let wish_count = $('.to-wish > div.products-in-wish');
                        prev_count = parseInt(wish_count.text());
                        wish_count.text(prev_count + 1);
                    }
                }
            }
        });
        btn.disabled = false;
    });

    $('button.cart.wishlist-btn.button-done').on('click', function () {
        let btn = this;
        btn.disabled = true;
        let endpoint = '/remove_favorite';
        $.ajax({
            headers: {"X-CSRF-Token": getCookie("csrf_access_token")},
            url: endpoint,
            method: 'post',
            data: JSON.stringify({id: parseInt(btn.getAttribute('data-product_id'), 10)}),
            contentType: "application/json",
            success: function (data) {
                if (data['success'] === 1) {
                    $(`#${btn.getAttribute('data-product_id')}.product.in-cart`).remove();
                    let wish_count = $('.to-wish > div.products-in-wish');
                    prev_count = parseInt(wish_count.text());
                    wish_count.text(prev_count - 1);
                } else {
                    btn.disabled = false;
                    alert('Не удалось удалить товар из списка');
                }
            }
        });
        btn.disabled = false;
    });
}

$('form#signin_form input[type="submit"]').on('click', function (event) {
    event.preventDefault();
    let form = $("#signin_form");
    $.ajax({
        url: '/login',
        data: form.serialize(),
        method: 'post',
        success: function(data)
        {
            if (data.success === 1) {
                close_window();
                location.reload();
            } else {
                if (data.error) {
                    let signin_errors = $("#signin_errors");
                    signin_errors.show();
                    signin_errors.text(data.error);
                }
            }
        }
    });
});

$('form#signup_form input[type="submit"]').on('click', function (event) {
    event.preventDefault();
    let form = $("#signup_form");
    $.ajax({
        url: '/register',
        data: form.serialize(),
        method: 'post',
        success: function(data)
        {
            if (data.success === 1) {
                close_window();
                location.reload();
            } else {
                if (data.error) {
                    let signup_errors = $("#signup_errors");
                    signup_errors.show();
                    signup_errors.text(data.error);
                }
            }
        }
    });
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

function sign_in() {
    content.style.filter = 'blur(2px)';
    signin_window['style'] = 'display: flex'
    signin_window.classList.add('show');
}

function sign_up() {
    content.style.filter = 'blur(2px)';
    signup_window['style'] = 'display: flex';
    signup_window.classList.add('show');
}

function sign_out() {
    $.ajax({
        headers: { "X-CSRF-Token": getCookie("csrf_access_token") },
        url: '/logout',
        method: 'post',
        success: function() {
            window.location.replace('/');
        }
    });
}

function close_window() {
    content.style.filter = '';
    let modals = $('.auth-wrapper');
    modals.removeClass('show');
    modals.css("display", "none")
    // modals.css("display", "none");
    $('ul.auth').css("display", "none");
}

function context_menu() {
    let context = $('.flex-container');
    console.log(context);
    if (context.hasClass('show')) {
        context.removeClass('show');
    } else {
        context.addClass('show');
    }
}

$('.search-form input[type="submit"], #fetch').on('click', function(event) {
    event.preventDefault();
    let s_form = $('.search-form')
    let s = s_form.serialize()
    if (window.location.pathname !== '/') {
        window.location.replace(`/?${s}`)
        return
    }
    let result_container = $('.offer > section')
    result_container.css('filter', 'blur(1px)');
    let args = $('.search-form, .left-filter :input,select').serialize() + '&html='
    $.ajax({
        url: '/query',
        data: args,
        method: 'get',
        contentType: "application/json",
        success: function(data)
        {
            result_container.css('filter', '');
            $('.products-title > h1').text(`Товаров найдено: ${data['total_count']}`);
            result_container.html(data['search_results']);
            bindProduct();
           bindWish();
           bindPaginationClick();
        }
    });
});

function bindPaginationClick() {
    $('li.pagination-widget__page').on('click', function () {
        let s_form = $('.search-form')
        let s = s_form.serialize()
        let result_container = $('.offer > section')
        result_container.css('filter', 'blur(1px)');
        let args = $('.search-form, .left-filter :input,select').serialize() + `&html=&start=${this.getAttribute('data-page-number')}`
        $.ajax({
            url: '/query',
            data: args,
            method: 'get',
            contentType: "application/json",
            success: function (data) {
                result_container.css('filter', '');
                $('.products-title > h1').text(`Товаров найдено: ${data['total_count']}`);
                result_container.html(data['search_results']);
                bindProduct();
                bindWish();
                bindPaginationClick();
            }
        });
    });
}
