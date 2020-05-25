# Consolidated Priority Tracker

The Consolidated Priority Tracker (CPT) is a real time tool that enables organizers to track their volunteers throughout the day. 

It addresses two deficiencies in technology during the 2018 campaign: 

First, VAN, our CRM, did not have an easy way to check people into events or add new people to events. As a result, this led to an initial Google Sheets infrastructure that allowed organizers to add new walk-in volunteers and check people into their volunteer shifts. The Sheets infrastructure, as well as this web app, also allowed organizers to track confirmation calls to volunteers throughout the day. This culminated into two features of the CPT: the Same Day Confirms and Flake Chase tabs. In each, users can edit the status of volunteers and track confirmation calls. At the end of the day, they can go to the review tab to sync those statuses back into VAN.

Second, VAN did not have an easy way to track paper canvassing operations in real time. As a result, seeing our real-time percent to goal was nearly impossible. In addition, organizers also had the responsibility of following up with canvassers every hour to check their progress, so they needed a way of tracking that as well. This is represented by the KPH tab, where one can see and edit the progress of each canvassing group.

In addition, there were many features that wound up being helpful for this feature to work:
- The Dashboard, which gives live metrics to admins
- User management, to allow managers to add new users more easily
- Further integrations with the CRM.
- Scheduled nightly jobs to send data to Google Sheets and to back up previous day's data.


Setup
====
If you haven't already, download [Python](https://www.python.org/downloads/)
  - For Mac OS, you can install using [homebrew](http://brew.sh/) with `brew install python`

We recommend running this on a virtual environment.

Run `pip3 install virtualenv` and then set up your virtual environment

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
    
Set configuration in `~/.bash_profile` (and then remember to `source` the file once you've updated it). For example:

    export DATABASE_URL=postgres://user:password@host:5432/database
    export schema=test
    export api_user=YOUR_VAN_API_USER
    export api_key=YOUR_VAN_API_KEY
    export secret_key=SOME_SECRET


Database Setup
====

Create a PostgreSQL database. Add a schema with the name you want.
In the `~/.bash_profile` file, add the schema name as the corresponding variable and set the DATABASE_URL to the new PostgreSQL database.

Then, run `python3 setup_db.py`.


Running Locally
====
Ensure that you are using your virtual environment (see above)

    source ./venv/bin/activate
    
For simple local use, run `python3 controller.py`
To create a version closer to Heroku, run `heroku local` to read from `Procfile`.

(Note that you *must use port 5000* or the OID redirect will not work and you may need to terminate other services like AirServer that are currently using that port)
    
Then navigate to http://localhost:5000/


Running on Heroku
====

1. Create a new app in Heroku. 
2. Deploy to Heroku using their instructions.
3. Add the config values you have locally to the Config in the Settings tab in Heroku.


Stack
====

- Python: basic server language
- PostgreSQL: the database language
- SqlAlchemy: translation service that translated python objects to Postgres
- Flask: Handles the web server element of the app for python
- Jinja: A flask-based templating system that creates the page structure
- Google OIDC: Authenticates users by requiring their login through a google account and matching it to our pre-determined list of users
- Socketio: Allows for live updates via a websocket that shows when other users make updates on a page and which users are presently viewing a page
- ProgressUI: This was our style library, thank you NGP VAN for making it publicly available
- Javascript/JQuery: Most of the client-side page interactions without a framework.
- Heroku: This service hosts this online and provides the basis for scheduled jobs, metrics, and logging.
- Loader.io: Used for load tests


VAN Integrations
====
In order to integrate with VAN, you will need to obtain a VAN api key from NGP VAN. Once you do, those values can be set as config. You can then uncomment some of the code here. You will also need to populate the ShiftStatus and EventType tables with their corresponding values.


Data Flow
====

Data flow went as follows: periodically throughout the day, we exported the Event Participant List in VAN of to the SyncShift table. The `helpers.py` functionality could run to put the latest data from SyncShifts into an accessible form for users. Nightly, the reset functionality would back up the previous day's shift, canvass group, and note data and import the next day's data into the shift and canvass group tables.