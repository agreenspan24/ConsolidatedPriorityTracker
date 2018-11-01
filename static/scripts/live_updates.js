// Hash of users currently on the page
// user_id => userData
var currentUsers = {};

// The current viewerInterval
var viewerInterval;
var intervalTimeout = 10000; // in ms

// The web socket
var socket;

/*
 * Connect to web socket and set up appropriate listeners
 *
 */

function configureWebSockets(office, page, userId) {
    if (window.location.protocol == "https:") {
      var wsScheme = "wss://";
    } else {
      var wsScheme = "ws://"
    };
    
    
    socket = io(wsScheme + location.host + '/live-updates');
    
    var json = { office: office, page: page }

    socket.on('connect', function () {
      console.log('Connected to WS!');
      socket.emit('join', json);
    });
    
    socket.emit('view', json);

    // TODO: this function timer should decay (instead of being called every 10s)
    clearInterval(viewerInterval);
    viewerInterval = setInterval( function() {
        // Send a heartbeat that we're alive
        socket.emit('view', json);
    
        // Check for stale users and delete/remove them when found
        staleUsers = findStaleUsers(currentUsers)
    
        for (var i = 0; i < staleUsers.length; i++) {
            // must first remove the icon and then delete from
            // the hash because we need the data
            removeUserIcon($('#current-viewers'), currentUsers[staleUsers[i]])
            delete currentUsers[staleUsers[i]]
        }
    
    }, intervalTimeout);
    
    socket.on('disconnect', function () {
        console.log('Disconnected from WS!');
    });
    
    
    // Triggered periodically for all viewers on this page
    socket.on('viewers', function (data) {
        // Update timestamp from local clock
        data['viewed_at'] = getCurrentTimestamp();
        // Add/update this user to the map
        currentUsers[data['user_id']] = data
        // Show the explanation
        $('#current-viewers .small').removeClass('hide');
        // Add the icon
        addUserIcon( $('#current-viewers'), '.users', data);
    });
    
    
    // This will be triggered whenever there is a change to the page
    socket.on('updates', function (data) {
        console.log('json: ' + JSON.stringify(data, null, 2));
    
        var itemRow = $('tr[data-item-id="' + data['item_id'] + '"]')
    
        // Don't disable the row if this an update we made
        if ( data['user_id'] != userId) {
            var phoneCells = itemRow.find('.phone, .cellphone');
            var phoneInput = itemRow.find('.phone input').first();
            var phoneInputId = phoneInput.attr('id');
            var cellphoneInput = itemRow.find('.cellphone input').first();
            var cellphoneInputId = cellphoneInput.attr('id');
            
            if (data['action_type'] == 'CLAIM') {
                // If a row has been claimed (not by this user), we're going
                // to grey it out and strike through the text as well as temporarily
                // hide any input elements (most of the show/hide logic is in the CSS)
                itemRow.addClass('claimed');
                var phoneInputVal = phoneInput.val();
                var cellphoneInputVal = cellphoneInput.val();
                if (phoneInputVal)
                    itemRow.find('.phone #' + phoneInputId + '-static').text(phoneInputVal);
                if (cellphoneInputVal) {
                    itemRow.find('.cellphone #' + cellphoneInputId + '-static').text(cellphoneInputVal);
                }
                // Also disable the claims link
                itemRow.find('.claims a').attr('disabled', 'disabled');
            } else if (data['action_type'] == 'UNCLAIM') {
                // Once the claim is removed, the input elements will become editable again
                itemRow.removeClass('claimed');
                // Also have to remove disabled on the links
                itemRow.find('a').removeAttr('disabled')
            } else {
                // The bg-red2 class needs to be added to the cells, not the row or it
                // will disappear on hover
                itemRow.addClass('edited');
                itemRow.find('.glyphicons.glyphicons-refresh').removeClass('hide');
                itemRow.find('a, input, select').attr('disabled', 'disabled');
            }
        } else {
            // If this user owns this particular row, let's stylize it so it's clear they do
            if (data['action_type'] == 'CLAIM') {
                itemRow.addClass('owns');
            } else if (data['action_type'] == 'UNCLAIM') {
                itemRow.removeClass('owns');
            }
        }
    
        // if this is a claim, put in the claim column, otherwise in editors column
        if (data['action_type'] == 'CLAIM') {
            itemRow.find('.claims a').text('');
            addUserIcon(itemRow, '.claims a', data);
        } else if (data['action_type'] == 'UNCLAIM') {
            removeUserIcon(itemRow, data);
            itemRow.find('.claims a').text('Claim');
        } else {
            addUserIcon(itemRow, '.editors', data);
        }
    
    });
    
}

/* 
 * Add a user icon to a particular point in the page
 * 
 * @params
 *  container:  the overall DOM element to search within
 *  target:     the class where the nodes should be inserted within container
 *  userData:  JSON representing the user
 */
function addUserIcon(container, targetClass, userData) {
    // Add the user icon to the editing section (far left)
    // (but first check that it's not already there)
    if ( container.find(targetClass + ' [data-user-id="' + userData['user_id'] + '"]').length == 0) {
        var user_color = (!userData['user_color'] ? '000000' : userData['user_color']);
        var user_icon = '<i class="user-icon" data-user-id="' + userData['user_id'] + 
                        '" data-viewed-at="' + userData['viewed_at'] + 
                        '" style="background-color: #' + user_color + '">' + 
                        userData['user_short_name'] + '</i>'
        container.find(targetClass).append(user_icon).addClass('fade-in');
    }
}

/* 
 * Remove a user icon from a container
 * 
 * @params
 *  container:  the overall DOM element to search within
 *  userData:  JSON representing the user
 */
function removeUserIcon(container, userData) {
    // Find and remove a user icon from a container
    container.find('[data-user-id="' + userData['user_id'] + '"]').remove();
}

/*
 * Get UNIX current time
 */
function getCurrentTimestamp() {
     return Math.round((new Date()).getTime() / 1000);
}


/* 
 * Find stale users
 * 
 * @params
 *  container:  the overall DOM element to search within
 *  userData:  JSON representing the user
 */
function findStaleUsers(user_map) {
    // we want to return the users that haven't been heard from in expire_seconds
    var expire_seconds = 30;

    var staleUsers = []

    // TODO: consider maintaining in a priority queue/min-heap instead of hash map
    for (var key in user_map) {
        // viewed_at and getCurrentTimestamp() are UNIX timestamps
        if (user_map[key]['viewed_at'] < getCurrentTimestamp() - expire_seconds) {
            console.log(user_map[key]['user_id'] + ' is stale and should be removed')
            staleUsers.push(user_map[key]['user_id']);
        }
    
    }

    return staleUsers;
}