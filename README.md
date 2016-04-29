**pacpartial** attempts to install or update packages on an out-of-date system using pacman.
Normally, you cannot install new software on a merely "refreshed" system, as the packages may require newer versions of their dependencies that are not present, leading to breakages.
Using this program ensures that the relevant packages are updated too.

Please note that this program can still cause breakages for a variety of reasons.
Check the [issue tracker][1] to see what they might be.
I recommend only using this if you are comfortable managing the package database and downgrading packages.

Make sure you read the manual (`man -l pacpartial.8`).

[1]: https://github.com/tmewett/pacpartial/issues
