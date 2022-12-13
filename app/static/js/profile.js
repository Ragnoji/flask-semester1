$('.profile-update button').on('click', function() {
   $.ajax({
       headers: {"X-CSRF-Token": getCookie("csrf_access_token")},
       url: '/user/update',
       method: 'post',
       data: $('#profile').serialize(),
       success: function(data) {
           if(data['success'] === 1) {
               alert('Изменения применены');
           } else {
               alert('Произошла ошибка при попытке применить изменения');
           }
       }
   });
});