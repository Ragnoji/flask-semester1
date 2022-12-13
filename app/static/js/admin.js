$('form button').on('click', function(event) {
   let form = $(`#${this.getAttribute('data-form-id')}`);
   $.ajax({
       headers: { "X-CSRF-Token": getCookie("csrf_access_token") },
       url: `/admin/${form.attr('id')}`.replaceAll('-', '_'),
       method: 'post',
       data: new FormData(form[0]),
       processData: false,
       contentType: false,
       success: function(data) {
          if(data['success'] !== 1) {
              alert(data['err']);
          } else {
              alert('Форма успешно обработана');
              location.reload();
          }
      }
   });
});

