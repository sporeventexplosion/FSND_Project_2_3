# Tournament Results Database and Python module
## Full Stack Nanodegree Project 2

A simple system for recording results for a tournament using the Swisis system. To run locally, follow the instructions below.

### How to Run

1. Ensure VirtualBox and Vagrant are installed.

2. `git clone` this repository into a directory with write access.

3. `cd` into the project directory you have just cloned and then into the `vagrant` directory.

4. Execute `vagrant up`. This may take a while if you do not already have the "ubuntu/trusty32" box downloaded. If you get an error related to port forwarding, make sure the ports 5050, 8000, and 808 are not currently being used by another process.

5. Execute `vagrant ssh`, and you will be logged in to the virtual machine automatically. If this does not work, try using a dedicated SSH program and connect to `localhost:2222` with username "vagrant" and password "vagrant".

6. Once connected, execute `cd /vagrant/tournament` in the SSH terminal.

7. Here, you can run `python` and import the tournament file for use, or you can run `python tournament_test.py` to validate that the functions in tournament.py are working probably.
