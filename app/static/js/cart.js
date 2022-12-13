$('.plus').on('click', function (event) {
    let id = this.getAttribute('data-pid');
    $.ajax({
        headers: { "X-CSRF-Token": getCookie("csrf_access_token") },
        url: '/cart/change_quantity',
        method: 'post',
        data: JSON.stringify({
            id: parseInt(id, 10),
            action: "+"
        }),
        contentType: "application/json",
        success: function (data) {
            if(data.success === 1){
                $(`#${id} .p_quantity`).text(data['p_qty'] + 'x');
                $(`#${id} .product-calculated-cost > span`).text(`~ ${data['p_cost'].toFixed(2)} ₽`);
                $('.cart-label.cart-cost').text(data['cost']);
                $('.products-in-cart').text(data['qty']);
            }
        }
    });
});

$('.minus').on('click', function (event) {
    let id = this.getAttribute('data-pid');
    $.ajax({
        headers: { "X-CSRF-Token": getCookie("csrf_access_token") },
        url: '/cart/change_quantity',
        method: 'post',
        data: JSON.stringify({
            id: parseInt(id, 10),
            action: "-"
        }),
        contentType: "application/json",
        success: function (data) {
            if(data.success === 1){
                $(`#${id} .p_quantity`).text(data['p_qty'] + 'x');
                $(`#${id} .product-calculated-cost > span`).text(`~ ${data['p_cost'].toFixed(2)} ₽`);
                $('.cart-label.cart-cost').text(data['cost']);
                $('.products-in-cart').text(data['qty']);
            } else if(data.success === 2) {
                $(`#${id}`).remove()
                if(data['qty'] !== 0) {
                    $('.cart-label.cart-cost').text(data['cost']);
                } else {
                    $('.cart-label.cart-cost').removeClass('cart-cost');
                    $('.cart-label').text('Корзина');
                    $('.cart-checkout').css('display', 'none');
                }
                $('.products-in-cart').text(data['qty']);
            }
        }
    });
});

$('button.checkout').on('click', function() {
   if(this.classList.contains('unauthorized')) {
       alert('Авторизуйтесь для создания заказа');
       sign_in();
   }
   $.ajax({
        headers: { "X-CSRF-Token": getCookie("csrf_access_token") },
        url: '/cart/checkout',
        method: 'post',
        contentType: "application/json",
        success: function (data) {
            if(data.success === 1) {
                window.location.replace('/');
                alert('Заказ успешно создан');
            } else {
                alert('Ошибка при создании заказа');
                window.location.reload();
            }
        }
    });
});