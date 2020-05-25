// Helper functions
function getParentIdFromId(id) {
    return id.split('-').pop();
}

function getRowElem(parent_id, name){
    return $('#' + name + '-' + parent_id);
}

function getName(parent_id) {
    return getRowElem(parent_id, 'name').text();
}

// POST the new value of the input to the server and handle its response
function updateElem(elem_id, elem_name, success_callback) {
    elem = $('#' + elem_id);
    var val = elem.val();

    var parent_id = getParentIdFromId(elem_id);
    var name = getName(parent_id);

    showAlert('info', 'Updating ' + elem_name + ' for ' + name);
    elem.prop('disabled', 'disabled');

    var data = {
        parent_id: parent_id,
        page_load_time: $("#page_load_time").text()
    };

    data[elem_name] = val;

    if (elem_name == 'cellphone') {
        shift_id = elem_id.split('-')[1];
        data['vol_id'] = getRowElem(shift_id, 'vol_id').text().replace(/,/, '');
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

// Success callbacks after updating values

// Append note to the end of the row
function addNote(parent_id, note, elem) {
    var child = document.createElement('td');
    child.innerText = note;
    getRowElem(parent_id, 'row').append(child);
    
    if (elem.attr('name') == 'note') {
        elem.val('');
    }
}

// Update the Percent to Goal value
function updateGoalActual(parent_id, res, elem) {
    var perc = getRowElem(parent_id, 'actual').val() / getRowElem(parent_id, 'goal').val();
    getRowElem(parent_id, 'perc').text(Math.round(perc * 10000) / 100 + '%');
}

// Update the check-in times, add a note, and update the PTG
function updateCheckInTimes(parent_id, res, elem) {
    if (!res.is_returned) {
        getRowElem(parent_id, 'check_in_time').text(res.check_in_time);
        getRowElem(parent_id, 'last_check_in').text(res.last_check_in);
        getRowElem(parent_id, 'check_ins').text(res.check_ins);
    }
    
    updateGoalActual(parent_id, res, elem);
    addNote(parent_id, res.note, elem);
}

// Update the shift's number of "passes", i.e. the amount of times they've called them.
function updatePasses(parent_id, res, elem) {
    getRowElem(parent_id, 'passes').text(res);
}

// Update the rows of information for the members of a canvass group when a member is added or deleted.
function updateNames(parent_id, res, elem) {
    var vol_id = '';
    var vanid = '';
    var name = '';
    var phone = '';
    var cellphone = ''; 

    res.forEach(function(shift, index) {
        vol_id += '<p id="vol_id-' + shift.id + '">'+ shift.vol_id + ',</p>';
        vanid += '<p id="shift-' + shift.id + '">'+ shift.van_id + '</p>';
        name += '<span>'+ shift.name + '</span>';
        phone += '<p>'+ shift.phone + '</p>';
        cellphone += '<p><input id="cell-' + shift.id + '" name="cellphone" maxlength="120"' +
            'type="text" style="width:125px" value="' + (shift.cellphone || '') + '"/></p>';
    });

    getRowElem(parent_id, 'vol_id').html(vol_id);
    getRowElem(parent_id, 'vanid').html(vanid);
    getRowElem(parent_id, 'name').html(name);
    getRowElem(parent_id, 'phone').html(phone);
    getRowElem(parent_id, 'cellphone').html(cellphone);
}

// Mark the canvass operation times as done or not done. Show the future shifts modal if necessary.
function beginOrEndCanvassGroup(parent_id, res, elem) {
    getRowElem(parent_id, 'out').text(res.is_returned ? 'Not Final' : 'Final');
    getRowElem(parent_id, 'check_in_time').text(res.check_in_time);
    getRowElem(parent_id, 'last_check_in').text(res.last_check_in);
    getRowElem(parent_id, 'check_ins').text(res.check_ins);
    getRowElem(parent_id, 'departure').val(res.departure);

    if (!res.check_in_time) {
        getRowElem(parent_id, 'departure').prop('disabled', 'disabled');

        show_future_shifts_modal(null, false, getRowElem(parent_id, 'vol_id').text().trim().replace(/\s/g, '').split(','));
    } else {
        getRowElem(parent_id, 'actual').prop('disabled', false);
        getRowElem(parent_id, 'departure').prop('disabled', false);
    }
}
 
// Listen for Enter or Tab to be hit on one of the input values that can be updated on the page.
// Update the values in the server if necessary and add the proper callback.
function setUpListener() {
    $('td input').on('keydown', function(e) {
        if (e.target.className == 'input-element') {
            return;
        }

        // Key Codes Enter or Tab
        if (e.keyCode == 13 || e.keyCode == 9) {
            var name = e.target.attributes['name'].nodeValue;
            var id = event.target.id;

            var success_callback = null;

            switch (name) {
                case 'note':
                    success_callback = addNote;
                    break;
                case 'departure':
                case 'actual':
                    success_callback = updateCheckInTimes;
                    break;
                case 'goal':
                    success_callback = updateGoalActual;
                    break;
                case 'first_name':
                case 'last_name':
                case 'phone':
                case 'cellphone':
                case 'packets_given':
                case 'packet_names':
                case 'vanid':
                    break;
                default:
                    return;
            }

            updateElem(id, name, success_callback);
        }
    });
}

$(document).ready(setUpListener);

// Delete the shift or canvass group
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

// Used for the Review tab, to remove the person from the values that will be updated in the CRM
function deleteRow(row) {
    $('#' + row).remove();
}

// Confirm a shift in the future directly in the CRM
function confirm_shift(e) {
    vanid = e.target.attributes['vanid'].nodeValue;
    time = e.target.attributes['time'].nodeValue;
    date = e.target.innerText;

    if (!vanid || !date || !time) return;

    if (window.confirm('Are you sure you want to confirm this person for this shift?')) {
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

function show_future_shifts_modal(event, is_update, vol_ids) {
    open_modal('future_shifts_modal');
    hideModalAlert();

    $('#future_shifts_head').addClass("hide");
    $('#future_shifts_body').text('');

    if (!is_update) {
        $('#group_vol_dropdown').addClass('hide');
    }

    $.ajax({
        type: 'POST', 
        url: window.location.pathname + '/future_shifts',
        data: {
            vol_ids: vol_ids || [event.target.value]
        }
    }).done(function(res) {
        if (res.vols) {
            if (!is_update && res.vols.length > 1) {
                var options = '';
                res.vols.forEach(function(x){
                    options += '<option value="' + x.id + '">' + x.first_name + ' ' + x.last_name + '</option>'
                });
                
                $('#vol_options').html(options);
                $('#group_vol_dropdown').removeClass('hide');
            }

            set_future_shifts_for_vol(res.vols[0], res.shifts);
        } else {
            showModalAlert('warn', 'Could not find volunteer.');
        }
    }).fail(function() {
        showModalAlert('error', 'There was an error getting shifts.');
    });
}

function set_future_shifts_for_vol(vol, shifts) {
    var name = vol.first_name + ' ' + vol.last_name;
    $('#future_shifts_name').text(name);

    if (vol.has_pitched_today) {
        $('#has_pitched_today').attr('checked', 'checked');
        $('#has_pitched_today').prop('checked', 'checked');
    } else {
        $('#has_pitched_today').removeAttr('checked');
        $('#has_pitched_today').prop('checked', false);
    }
    
    $("#extra_shifts_sched").val(vol.extra_shifts_sched);
    $('#future_shifts_history_link').attr('href', '/consolidated/volunteer_history/' + vol.id);

    if (vol.code) {
        $('#future_shifts_contact_details').removeClass('hide');
        $('#future_shifts_event_scheduler').removeClass('hide');
        $('#future_shifts_contact_details').attr('href', 'https://www.votebuilder.com/ContactsDetails.aspx?VanID=' + vol.code);
        $('#future_shifts_event_scheduler').attr('href', 'https://www.votebuilder.com/EventScheduler.aspx?VanID=' + vol.code);
    } else {
        $('#future_shifts_contact_details').addClass('hide');
        $('#future_shifts_event_scheduler').addClass('hide');
    }

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

    if (!vol.van_id){
        showModalAlert('warn', 'No vanid for volunteer. Please add one and schedule them for shifts in VAN.')
    } else if (shifts.length == 0) {
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