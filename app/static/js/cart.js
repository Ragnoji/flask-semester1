let plus = document.querySelectorAll('.plus');
let minus = document.querySelectorAll('.minus');

plus.forEach(button => {
    button.addEventListener('click', function (event) {
        event.preventDefault();
        let id = this.name
        $.ajax({
            headers: { "X-CSRFToken": token },
            url: '/cart/change_quantity',
            method: 'post',
            data: {
                id: this.name,
                action: '+'},
            success: function (data) {
                let count = document.getElementById(id);
                let count_cart = $('.products-in-cart')[0];
                count.innerText = data.count;
                count_cart.innerText = parseInt(count_cart.innerText) + 1;
            }
        });
    });
});

minus.forEach(button => {
    button.addEventListener('click', function (event) {
        event.preventDefault();
        let id = this.name
        let count = document.getElementById(id);
        if (count.innerText === '0') {
            return
        }
        $.ajax({
            headers: { "X-CSRFToken": token },
            url: '/cart/change_quantity',
            method: 'post',
            data: {
                id: this.name,
                action: '-'},
            success: function (data) {
                let count = document.getElementById(id);
                let count_cart = $('.products-in-cart')[0];
                count.innerText = data.count;
                count_cart.innerText = parseInt(count_cart.innerText) - 1;
            }
        });
    });
});