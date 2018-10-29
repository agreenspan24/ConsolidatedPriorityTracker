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

        showAlert('error', message);
        elem.prop('disabled', false);
    });
}

// success callbacks
function addNote(parent_id, res, elem) {
    var child = document.createElement('td');
    child.innerHTML = res;
    getRowElem(parent_id, 'row').append(child);
    
    if (elem.attr('name') == 'note') {
        elem.val('');
    }
}

function updateGoalActual(parent_id, res, elem) {
    var perc = getRowElem(parent_id, 'actual').val() / getRowElem(parent_id, 'goal').val();
    getRowElem(parent_id, 'perc').html(Math.round(perc * 10000) / 100 + '%');
}

function updateCheckIns(parent_id, res, elem) {
    if (!res.is_returned) {
        getRowElem(parent_id, 'check_in_time').html(res.check_in_time);
        getRowElem(parent_id, 'last_check_in').html(res.last_check_in);
        getRowElem(parent_id, 'check_ins').html(res.check_ins);
    }
    
    updateGoalActual(parent_id, res, elem);
    addNote(parent_id, res.note, elem);
}

function updatePasses(parent_id, res, elem) {
    getRowElem(parent_id, 'passes').html(res);
}

function updateNames(parent_id, res, elem) {
    var vanid = '';
    var name = '';
    var phone = '';
    var cellphone = ''; 

    res.forEach(function(shift, index) {
        vanid += '<p id="shift-' + shift.id + '">'+ shift.van_id + '</p>';
        name += '<span>'+ shift.name + '</span>';
        phone += '<p>'+ shift.phone + '</p>';
        cellphone += '<p><input id="cell-' + shift.id + '" name="cellphone" maxlength="120"' +
            'type="text" style="width:125px" value="' + (shift.cellphone || '') + '"/></p>';
    });

    getRowElem(parent_id, 'vanid').html(vanid);
    getRowElem(parent_id, 'name').html(name);
    getRowElem(parent_id, 'phone').html(phone);
    getRowElem(parent_id, 'cellphone').html(cellphone);
}

function setOut(parent_id, res, elem) {
    getRowElem(parent_id, 'out').html(res.is_returned ? 'Not Final' : 'Final');
    getRowElem(parent_id, 'check_in_time').html(res.check_in_time);
    getRowElem(parent_id, 'last_check_in').html(res.last_check_in);
    getRowElem(parent_id, 'check_ins').html(res.check_ins);
    getRowElem(parent_id, 'departure').val(res.departure);

    if (!res.check_in_time) {
        getRowElem(parent_id, 'departure').prop('disabled', 'disabled');

        get_future_shifts(null, false, getRowElem(parent_id, 'vanid').text().trim().replace(' ', ',').replace(/\s/g, '').split(','));
    } else {
        getRowElem(parent_id, 'actual').prop('disabled', false);
        getRowElem(parent_id, 'departure').prop('disabled', false);
    }
}

function updateClaim(parent_id, res, elem) {
    if (res.name !== 'Claim') {
        html = '<i class="user-icon" style="background-color:#' + (res.color || '000000') + '">' + res.name + '</i>';
    } else {
        html = res.name;
    }

    getRowElem(parent_id, 'claim').html(html);
}
 
function setUpListener() {
    $('td input').on('keydown', function(e) {
        if (e.target.className == 'input-element') {
            return;
        }

        if (e.keyCode == 13 || e.keyCode == 9) {
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
                updateElem(id, name, updateCheckIns);
            } else if (name == 'goal') {
                updateElem(id, name, updateGoalActual);
            } else if (name == 'packets_given') {
                updateElem(id, name, null);
            } else if (name == 'packet_names') {
                updateElem(id, name, null);
            } else if (name == 'departure') {
                updateElem(id, name, updateCheckIns);
            } else if (name == 'vanid') {
                updateElem(id, name, null);
            }
        }
    });
}

$(document).ready(setUpListener);

function show_recently_updated(elements) {
    elements.forEach(function(element) {
        updateClaim(element.id, element);

        if (element.updated) {
            getRowElem(element.id, 'row').addClass('bg-red2');
            $('#row-' + element.id + ' .glyphicons.glyphicons-refresh').removeClass('hide');
            getRowElem(element.id, 'claim').attr('disabled');
        }
        else {
            getRowElem(element.id, 'claim').removeAttr('disabled');
        }
    });
}

function get_recently_updated() {
    $.ajax({
        type: 'GET', 
        url: window.location.pathname + '/recently_updated',
        data: {
            page_load_time: $("#page_load_time").html()
        }
    }).done(show_recently_updated)
    .fail(function(res){
        var message = 'Could not get recently updated rows. Please refresh the page.';

        if (res.responseText) {
            message += ' Error message: ' + res.responseText
        }
        
        showAlert('error', message);
    });
}

if (!window.location.pathname.endsWith('review')) {
    setInterval(get_recently_updated, 20000);
}

function deleteElement(parent_id) {
    if (confirm('Are you sure you want to delete this row?')) {
        $.ajax({
            type: 'DELETE', 
            url: window.location.pathname + '/delete_element',
            data: {
                parent_id: parent_id
            }
        }).done(function (name) {
            showAlert('success', 'Deleted ' + name + ' from the database.');
    
            $('#row-' + parent_id).remove();
        }).fail(function (res) {
            var message = 'Could not delete.';
    
            if (res.responseText) {
                message += ' Error message: ' + res.responseText
            }
            
            showAlert('error', message);
        });
    }
}

function deleteNote(shift_id, text) {
    $.ajax({
        type: 'DELETE', 
        url: window.location.pathname + '/delete_note',
        data: {
            shift_id: shift_id,
            text: text
        }
    }).done(function () {
        showAlert('success', 'Deleted note "' + text + '" from the database.');


        if (window.location.pathname.endsWith('kph')) {
            $('td#notes-' + shift_id + ':contains("' + text + '")').remove();
        } else {
            $('#row-' + shift_id + ' > td:contains("' + text + '")').remove();
        }
    }).fail(function (res) {
        var message = 'Could not delete note.';

        if (res.responseText) {
            message += ' Error message: ' + res.responseText
        }
        
        showAlert('error', message);
    });
}

function deleteRow(row) {
    $('#' + row).remove();
}

function confirm_shift(e) {
    vanid = e.target.attributes['vanid'].nodeValue;
    time = e.target.attributes['time'].nodeValue;
    date = e.target.innerText;

    if (!vanid || !date || !time) return;

    if (confirm('Are you sure you want to confirm this person for this shift?')) {
        showAlert('info', 'Updating next shift for ' + vanid);

        $.ajax({
            type: 'POST',
            url: window.location.pathname + '/confirm_shift',
            data: {
                vanid,
                date: date + ' ' + time
            }
        }).done(function() {
            showAlert('success', 'Updated next shift for ' + vanid);
            showModalAlert('success', 'Updated next shift for ' + vanid);
            
            e.target.innerHTML += '&nbsp;<span class="glyphicons glyphicons-ok text-green7"></span>';
        }).fail(function(res) {
            var message = 'Could not update next shift.';

            if (res.responseText) {
                message += ' Error message: ' + res.responseText
            }
            
            showAlert('error', message);
            showModalAlert('error', message);
        });
    }
}

function get_future_shifts(event, is_update, vanids) {

    open_modal('future_shifts_modal');
    hideModalAlert();

    $('#future_shifts_head').addClass("hide");
    $('#future_shifts_body').html('');

    if (!is_update) {
        $('#group_vol_dropdown').addClass('hide');
    }

    $.ajax({
        type: 'POST', 
        url: window.location.pathname + '/future_shifts',
        data: {
            vanids: vanids || [event.target.value]
        }
    }).done(function(res) {
        if (res.vols) {
            if (!is_update && res.vols.length > 1) {
                var options = '';
                res.vols.forEach(function(x){
                    options += '<option value="' + x.van_id + '">' + x.first_name + ' ' + x.last_name + '</option>'
                });
                
                $('#vol_options').html(options);
                $('#group_vol_dropdown').removeClass('hide');
            }

            set_future_shifts_for_vol(res.vols[0], res.shifts);
        } else {
            $('#future_shifts_body').html('<p>Could not find volunteer</p>');
        }
    }).fail(function() {
        $('#future_shifts_body').html('<p>There was an error getting shifts</p>');
    });
}

function set_future_shifts_for_vol(vol, shifts) {
    $('#future_shifts_name').html(vol.first_name + ' ' + vol.last_name);

    $('#has_pitched_today').removeAttr('checked');
    $('#has_pitched_today').attr('checked', (vol.has_pitched_today ? 'checked' : false));
    $("#extra_shifts_sched").val(vol.extra_shifts_sched);
    $('#future_shifts_history_link').attr('href', '/consolidated/volunteer_history/' + vol.id);
    $('#update_vol_pitch').attr('vol_id', vol.id);

    var rowTemplate = 
    "<tr>" +
        "<td>{0}</td>" +
        "<td>{1}</td>" + 
        "<td vanid='{5}' time='{3}' ondblclick='confirm_shift(event)' style='cursor:pointer'>{2}&nbsp;<span class='glyphicons glyphicons-ok text-green7 {6}'></span></td>" + 
        "<td>{3}</td>" + 
        "<td>{4}</td>" + 
    "</tr>";

    var rows = '';

    var exp_shifts = ((Date.parse('2018-11-06') - Date.now()) / (60 * 60 * 24 * 1000)) / 2;

    if (shifts.length == 0) {
        showModalAlert('error', 'Oops! ' + name + ' has no future shifts! Schedule them right away!');
    } else if (shifts.length < exp_shifts) {
        showModalAlert('warn', 'Oh no! ' + name + " doesn't has enough shifts scheduled! They should have about " + Math.round(exp_shifts - shifts.length) + ' more shifts.');
    }

    shifts.forEach(function(s) {
        if (s.vanid == vol.van_id) {
            rows += rowTemplate
                .replace('{0}', s.eventtype)
                .replace('{1}', s.locationname)
                .replace('{2}', s.startdate)
                .replace(/\{3\}/g, s.starttime)
                .replace('{4}', s.status)
                .replace('{5}', s.vanid)
                .replace('{6}', (s.status == 'Confirmed' ? '' : 'hide'));
        }
    });

    if (shifts.length > 0) {
        $('#future_shifts_head').removeClass("hide");
    }

    $('#future_shifts_body').html(rows);
}

function update_vol_pitch(event) {
    vol_id = event.target.attributes['vol_id'].nodeValue;

    $.ajax({
        type: 'POST', 
        url: window.location.pathname + '/vol_pitch',
        data: {
            vol_id: vol_id, 
            has_pitched_today: $('#has_pitched_today').val(),
            extra_shifts_sched: $('#extra_shifts_sched').val()
        }
    }).done(function() {
        showModalAlert('success', 'Pitch information updated');
    }).fail(function(res) {
        showModalAlert('error', 'Pitch information could not be updated. ' + res);
    });

}