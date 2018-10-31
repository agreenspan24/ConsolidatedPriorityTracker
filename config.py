import os
settings = {
    "sql_username" : "consolidated",
    "sql_pass" : "QE4cq&%L42wb",
    "secret_key" : "fasdjhkR#$@sdaf",
    "server" : 'reporting.czrfudjhpfwo.us-east-2.rds.amazonaws.com:5432/mcc'
    #"regions" : {'NV' : "West", 'GA' : 'South', 'IA' : 'Midwest', 'NH' : 'Northeast', 'TN' : 'Central' },
    #"event_types" : ["Volunteer DVC", "Phonebanking", "Vol Recruitment"],
    #"event_status" : {"Scheduled" : 1, "Tentative" : 14, "Confirmed" : 11, "Completed" : 2, "Declined" : 3, "No Show" : 6, "Resched" : 26, "Left Msg" : 18 }
}

test_settings = {
    "sql_username" : "zmteqmujvkfnmq",
    "sql_pass" : "8dce67c5ae02028c174df35be856535c90a9593280ab43edceadf25f3f76f97a",
    "secret_key" : "fasdjhkR#$@sdaf",
    "server" : 'ec2-54-83-204-230.compute-1.amazonaws.com/de8kcah93s00d9'
    #"regions" : {'NV' : "West", 'GA' : 'South', 'IA' : 'Midwest', 'NH' : 'Northeast', 'TN' : 'Central' },
    #"event_types" : ["Volunteer DVC", "Phonebanking", "Vol Recruitment"],
    #"event_status" : {"Scheduled" : 1, "Tentative" : 14, "Confirmed" : 11, "Completed" : 2, "Declined" : 3, "No Show" : 6, "Resched" : 26, "Left Msg" : 18 }
}

os.environ['api_key'] = '383b5e54-4374-2059-414f-698c1045fb2c'
os.environ['api_user'] = 'mdp.internal.api'
os.environ['HEROKU_POSTGRESQL_AMBER_URL'] = 'postgres://udq8m08n6hjmcm:p3d9b763d9c7c20258eeca3568605c92a55d0aa84c8b6a6a63ded7a787f65e4a4@ec2-23-20-55-108.compute-1.amazonaws.com:5432/d2970fhsvk9kkq'
os.environ['secret_key'] = 'fasdjhkR#$@sdaf'

schema = 'test'


 