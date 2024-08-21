$(document).ready(function() {
    $('.buttonsSendCmd').on('click', function() {
        // Dati arbitrari da inviare
        var command = $(this).attr('data-cmd');
        var param = $(this).attr('data-param');

        var iotId = $(this).attr('data-iot-id');

        var payload = {
            cmd: command,
            param: param,
        };

        $.post('/api/' + iotId + '/command', payload, function(response) {
            // Gestisci la risposta del server qui
            console.log('Server responded with:', response);
        }).fail(function(jqXHR, textStatus, errorThrown) {
            // Gestisci gli errori qui
            console.error('Request failed:', textStatus, errorThrown);
        });
    });
});