function open_modal(id){
    $('.modal-wrapper').addClass('modal-backdrop fade in');
    $('#' + id).show();
}

function hide_modal() {
    $('.modal-wrapper').removeClass('modal-backdrop fade in');
    $('.modal').hide();
}

function maybe_hide_modal(e) {
    if (e.target.className.startsWith('modal ')) {
        hide_modal();
    }
}

function showModalAlert(type, text) {
    hideModalAlert();

    $('#modal-alert').removeClass('hide success info warn error').addClass(type);
    $('#modal-alert-text').html(text);
}

function hideModalAlert() {
    $('#modal-alert').addClass('hide');
}

function update_vol_pitch(event) {
    vol_id = event.target.attributes['vol_id'].nodeValue;

    $.ajax({
        type: 'POST', 
        url: window.location.pathname + '/vol_pitch',
        data: {
            vol_id: vol_id, 
            has_pitched_today: $('#has_pitched_today:checked').length ? "True" : "False",
            extra_shifts_sched: $('#extra_shifts_sched').val()
        }
    }).done(function() {
        showModalAlert('success', 'Pitch information updated');
    }).fail(function(res) {
        showModalAlert('error', 'Pitch information could not be updated. ' + res);
    });
}