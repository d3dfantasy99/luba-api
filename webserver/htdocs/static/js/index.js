document.addEventListener('DOMContentLoaded', function() {
    
    function fetchDataAndUpdateSpan() {
        fetch(url)
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok ' + response.statusText);
                }
                return response.json();
            })
            .then(data => {
                data = data.data;
                if (data.hasOwnProperty('device')) {
                    // Imposta il valore dello span
                    document.getElementById('battery_status').textContent = data.device.battery_status;
                    document.getElementById('wifiRSSI').textContent = data.device.wifiRSSI;
                    document.getElementById('bleRSSI').textContent = data.device.bleRSSI;
                    document.getElementById('robot_status').textContent = data.device.robot_status;
                }

                if (data.hasOwnProperty('rtk')) {
                    // Imposta il valore dello span
                    document.getElementById('pos_status').textContent = data.rtk.pos_status;
                    document.getElementById('robot_sat').textContent = data.rtk.robot_sat;
                    document.getElementById('ref_station_sat').textContent = data.rtk.ref_station_sat;
                    document.getElementById('co_view_sat').textContent = data.rtk.co_view_sat;
                    document.getElementById('signal_quality_robot').textContent = data.rtk.signal_quality_robot;
                    document.getElementById('signal_quality_ref_station').textContent = data.rtk.signal_quality_ref_station;
                    document.getElementById('lora_status').textContent = data.rtk.lora_status;
                    document.getElementById('lora_number').textContent = data.rtk.lora_number;
                }

                if (data.hasOwnProperty('location')) {
                    // Imposta il valore dello span
                    if(data.location.hasOwnProperty('lat'))
                        document.getElementById('lat').textContent = data.location.lat;
                    if(data.location.hasOwnProperty('lon'))
                        document.getElementById('lon').textContent = data.location.lon;
                }

                if (data.hasOwnProperty('work')) {
                    // Imposta il valore dello span
                    if(data.work.hasOwnProperty('total_area'))
                        document.getElementById('total_area').textContent = data.work.total_area;
                    if(data.work.hasOwnProperty('mowing_speed'))
                        document.getElementById('mowing_speed').textContent = data.work.mowing_speed;
                    if(data.work.hasOwnProperty('progress'))
                        document.getElementById('progress').textContent = data.work.progress;
                    if(data.work.hasOwnProperty('total_time'))
                        document.getElementById('total_time').textContent = data.work.total_time;
                    if(data.work.hasOwnProperty('elapsed_time'))
                        document.getElementById('elapsed_time').textContent = data.work.elapsed_time;
                    if(data.work.hasOwnProperty('left_time'))
                        document.getElementById('left_time').textContent = data.work.left_time;
                    if(data.work.hasOwnProperty('blade_height'))
                        document.getElementById('blade_height').textContent = data.work.blade_height;

                }

            })
            .catch(error => {
                console.error('There was a problem with the fetch operation:', error);
            });
    }

    fetchDataAndUpdateSpan();

    setInterval(fetchDataAndUpdateSpan, 5000);
});
