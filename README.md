# Fullstack Nanodegree Virtual Machine environment

## Prepare VM environment

1. Ensure VirtualBox and Vagrant are installed.

2. `git clone` this repository into a directory with write access.

3. `cd` into the project directory you have just cloned and then into the `vagrant` directory.

4. Execute `vagrant up`. This may take a while if you do not already have the "ubuntu/trusty32" box downloaded. If you get an error related to port forwarding, make sure the ports 5050, 8000, and 8080 are not currently being used by another process.

5. Execute `vagrant ssh`, and you will be logged in to the virtual machine automatically. If this does not work, try using a dedicated SSH program and connect to `localhost:2222` with username "vagrant" and password "vagrant".

## Full Stack Nanodegree Project 2
Tournament Results Database and Python module

A simple system for recording results for a tournament using the Swiss system. To run locally, follow the instructions below.

### How to Run

1. Clone and connect to the VM as explained above.

2. Execute `cd /vagrant/tournament` in the SSH terminal.

3. Here, you can run `python` and import the tournament file for use, or you can run `python tournament_test.py` to validate that the functions in tournament.py are working properly.

## Full Stack Nanodegree Project 3
Catalog Web App

A web application for creating, reading, updating and deleting items organized within categories. Includes a login system implementing third-party login APIs.

### How to Run

1. Clone and connect to the VM as explained above.

2. Execute `cd /vagrant/catalog` in the SSH terminal.

3. Run `python database_setup.py` to set up the SQLite database used by this website.

4. Run `python app.py` to start the web server. Port 5000 will be forwarded to your host machine and you can access the site on `http://localhost:5000/` in a browser.
