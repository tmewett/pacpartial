**pacpartial** attempts to integrate newly installed or upgraded packages into an out-of-date system using pacman.
Normally, you cannot install new software on a merely "refreshed" system, as the packages may require newer versions of API/ABIs that are not present, leading to breakages.
Using this program ensures that the relevant dependencies (and their deps, etc.) are updated too.

Please note that this program is in its early stages, and it MAY still cause breakages.
Only use this if you know how to recover a system and downgrade packages.

Make sure you read the manual (`man -l pacpartial.8`).
