# Priority Tracker

Priority Tracker is a real time tool that enables organizers to track their volunteers throughout the day, including check in calls, and knocks per shift.

Setup
====
After cloning run `pip3 install virtualenv` and then set up your virtual environment

    virtualenv -p python3 venv

(.If you have trouble building the virtalenv, try running `pip3 install --upgrade pip`
and `pip3 install --upgrade setuptools` to install the latest version of `pip3` and
`setuptools` respectively.)

Active the virtual environment by running:

    source ./venv/bin/activate

Then install the necessary dependencies.

    pip3 install -r requirements.txt
    
If you encouter errors, ensure the PostgreSQL client and developer extensions as
well as gcc are all installed.

For Mac OS, ensure the OS X command line developer tools (`xcode-select --install`) and [homebrew](http://brew.sh/) have been installed and then run:

    brew install gcc postgresql
    
Set configuration in `~/.bashrc` (and then remember to `source` the file once you've updated it). For example:

    export HEROKU_POSTGRESQL_AMBER_URL=postgres://user:password@host:5432/database
    export schema=test
    export api_user=SOME_API_USER
    export api_key=SOME_API_KEY
    export secret_key=SOME_SEKRIT

Running
====
Ensure that you are using your virtual environment (see above)

    source ./venv/bin/activate
    
Run `gunicorn -b 0.0.0.0:5000 -w 6 controller:app --reload` (or `heroku local` to read from `Procfile`)

(Note that you *must use port 5000* or the OID redirect will not work and you may need to terminate other services like AirServer that are currently using that port)
    
Then navigate to http://localhost:5000/