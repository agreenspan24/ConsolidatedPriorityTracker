// helper functions
function getParentIdFromId(id) {
    return id.split('-').pop();
}

function getRowElem(parent_id, name){
    return $('#' + name + '-' + parent_id);
}

function getName(parent_id) {
    return getRowElem(parent_id, 'name').html();
}

function updateElem(elem_id, elem_name, success_callback) {
    elem = $('#' + elem_id);
    var val = elem.val();

    var parent_id = getParentIdFromId(elem_id);
    var name = getName(parent_id);

    showAlert('info', 'Updating ' + elem_name + ' for ' + name);
    elem.prop('disabled', 'disabled');

    var data = {
        parent_id: parent_id,
        page_load_time: $("#page_load_time").html()
    };

    data[elem_name] = val;

    if (elem_name == 'cellphone') {
        shift_id = elem_id.split('-')[1];
        data['vol_id'] = getRowElem(shift_id, 'vol_id').html();
    }

    $.ajax({
        type: 'POST', 
        url: window.location.pathname + '/pass',
        data: data
    }).done(function(res){
        showAlert('success', elem_name + ' for ' + name + ' has been updated');
        elem.prop('disabled', false);

        if (success_callback) {
            success_callback(parent_id, res, elem);
        }
    }).fail(function(res){
        var message = elem_name + ' for ' + name + ' has NOT been updated.';
        if (res.responseText) {
            message += ' Error message: ' + res.responseText
        }
        console.log(res);
        showAlert('error', message);
        elem.prop('disabled', false);
    });
}


// success callbacks
function addNote(parent_id, res, elem) {
    var child = document.createElement('td');
    child.innerText = res;
    getRowElem(parent_id, 'row').append(child);
    
    elem.val('');
}

function updateGoalActual(parent_id, res, elem) {
    var perc = getRowElem(parent_id, 'actual').val() / getRowElem(parent_id, 'goal').val();
    getRowElem(parent_id, 'perc').html(Math.round(perc * 10000) / 100 + '%');
}

function updateCheckIns(parent_id, res, elem) {
    getRowElem(parent_id, 'check_in').val('');
    getRowElem(parent_id, 'check_in_time').html(res.check_in_time);
    getRowElem(parent_id, 'last_check_in').html(res.last_check_in);
    getRowElem(parent_id, 'check_ins').html(res.check_ins);
    getRowElem(parent_id, 'actual').val(res.actual);

    updateGoalActual(parent_id, res, elem);

    addNote(parent_id, res.note);
}

function updateNames(parent_id, res, elem) {
    var vanid = '';
    var name = '';
    var phone = '';
    var cellphone = ''; 

    res.forEach(function(shift, index) {
        vanid += '<span id="shift-' + shift.id + '>'+ shift.van_id + '</span>';
        name += '<span>'+ shift.name + '</span>';
        phone += '<p>'+ shift.phone + '</p>';
        cellphone += '<p><input id="cell-' + shift.id + '" name="cellphone" maxlength="120"' +
            'type="text" value="' + (shift.cellphone || '') + '"/></p>';
    });

    getRowElem(parent_id, 'vanid').html(vanid);
    getRowElem(parent_id, 'name').html(name);
    getRowElem(parent_id, 'phone').html(phone);
    getRowElem(parent_id, 'cellphone').html(cellphone);
}

function setOut(parent_id, res, elem) {
    getRowElem(parent_id, 'out').html(res.is_returned ? 'Not Returned' : 'Returned');
    getRowElem(parent_id, 'check_in_time').html(res.check_in_time);
    getRowElem(parent_id, 'last_check_in').html(res.last_check_in);
    getRowElem(parent_id, 'check_ins').html(res.check_ins);
    getRowElem(parent_id, 'departure').html(res.departure);

    if (!res.check_in_time){
        getRowElem(parent_id, 'check_in').prop('disabled', 'disabled');
        getRowElem(parent_id, 'check_in').attr('disabled');
    } else {
        getRowElem(parent_id, 'check_in').removeAttr('disabled');
        getRowElem(parent_id, 'check_in').prop('disabled', false);
    }
}

function setUpListener() {
    $('body').on('keyup', function(e) {
        e.preventDefault();

        if (e.keyCode == 13) {
            var name = e.target.attributes['name'].nodeValue;
            var id = event.target.id;

            if (name == 'note') {
                updateElem(id, name, addNote);
            } else if (name == 'first_name') {
                updateElem(id, name, null);
            } else if (name == 'last_name') {
                updateElem(id, name, null);
            } else if (name == 'phone') {
                updateElem(id, name, null);
            } else if (name == 'cellphone') {
                updateElem(id, name, null);
            } else if (name == 'actual') {
                updateElem(id, name, updateGoalActual);
            } else if (name == 'goal') {
                updateElem(id, name, updateGoalActual);
            } else if (name == 'packets_given') {
                updateElem(id, name, null);
            } else if (name == 'packet_names') {
                updateElem(id, name, null);
            } else if (name == 'check_in') {
                updateElem(id, name, updateCheckIns);
            }
        }
    });
}

$(document).ready(setUpListener);