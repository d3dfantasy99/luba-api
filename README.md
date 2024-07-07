# luba HTTP Api (unofficial)

Work in progress (partially working)

## How to install

1. Download code
2. Install poetry (if not already installed)
3. Run the 'poetry install' command (in the project directory)
4. Edit the app.py file with your email and password (mammotion account)
5. Start script with 'poetry run python app.py'

## Endpoint for Json API

1. http://127.0.0.1:5000/api/devices -> return the list of devices linked to your account (take note of iotId)
2. http://127.0.0.1:5000/api/{iotid}/status -> (Replace iot id that you recovered from the previous step) -> Displays the device status (Raw data)
3. http://127.0.0.1:5000/api/{iotid}/status?format=human -> (Replace iot id that you recovered from the previous step) -> Displays the device status (Human readable data)

## Endpoint for Dashboard
2. http://127.0.0.1:5000/{iotid} -> (Replace iot id that you recovered from the previous step) - Html dashboard

## Legal Disclaimer
The software provided in this repository is offered "as-is" and the author makes no representations or warranties of any kind concerning the software, express or implied, including but not limited to warranties of merchantability, fitness for a particular purpose, or non-infringement. In no event shall the author be liable for any claim, damages, or other liability, whether in an action of contract, tort, or otherwise, arising from, out of, or in connection with the software or the use or other dealings in the software.

Users of this software assume all risks associated with its use, including but not limited to the risk of damage to hardware, loss of data, and account suspension or bans. The author disclaims any responsibility for any such consequences.

Trademark Notice

The trademarks "Mammotion," "Luba," and "Yuka" referenced herein are registered trademarks of their respective owners. The author of this software repository is not affiliated with, endorsed by, or connected to these trademark owners in any way.

By using this software, you agree to the terms of this disclaimer.
