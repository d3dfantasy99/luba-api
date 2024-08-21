async function showDevicesList() {
    try {
        // Esegui una richiesta GET al tuo endpoint JSON
        const response = await fetch('/api/devices');
        const data = await response.json();

        if (data.status) {
            if(data.data.length <= 0)
            {
                Swal.fire('Error', 'No device binded to your account', 'warning');
                return;
            }
             // Costruisci il contenuto HTML dinamicamente
            let swalContent = '<div id="swal-list">';
            data.data.forEach(item => {
                swalContent += `
                    <div class="swal-item" data-value="${item.iotID}">
                        <h4>${item.deviceName}</h4>
                        <p>${item.nick_name}</p>
                    </div>`;
            });
            swalContent += '</div>';

            // Mostra la finestra modale con il contenuto dinamico
            Swal.fire({
                title: 'Seleziona un elemento',
                html: swalContent,
                showConfirmButton: false,  // Nasconde il pulsante "OK"
                didRender: () => {
                    // Aggiungi event listener agli elementi della lista
                    document.querySelectorAll('.swal-item').forEach(item => {
                        item.addEventListener('click', () => {
                            const value = item.getAttribute('data-value');
                            window.location.href = "/" + value
                        });
                    });
                }
            });
        }
        else
        {
            Swal.fire('Error', data.error, 'error');
        }
       

    } catch (error) {
        console.error('Errore nel recupero dei dati:', error);
        Swal.fire('Error', 'Can\'t retrive your devices. Try again later', 'error');
    }
}