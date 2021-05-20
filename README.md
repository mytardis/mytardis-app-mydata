# mytardis-app-mydata

[![Build](https://github.com/mytardis/mytardis-app-mydata/workflows/Test%20MyTardis%20MyData%20App/badge.svg)](https://github.com/mytardis/mytardis-app-mydata/actions?query=workflow%3A%22Test+MyTardis+MyData+App%22) [![codecov](https://codecov.io/gh/mytardis/mytardis-app-mydata/branch/master/graph/badge.svg)](https://codecov.io/gh/mytardis/mytardis-app-mydata)

Server-side functionality and data models for MyData

This app should be installed in "tardis/apps/mydata":
```
cd /opt/mytardis/develop/tardis/apps
git clone https://github.com/mytardis/mytardis-app-mydata mydata
```
When cloning the repository above, ensure that you clone the
"mytardis/mytardis-app-mydata" repository as described above,
NOT the "mytardis/mydata" repository.

Run "pip install -r requirements.txt" from the "tardis/apps/mydata" 
directory to install the extra Python module dependencies required by the 
"mytardis-app-mydata" app. If you are not using a virtualenv for your 
MyTardis Python module dependencies, then you may need use "sudo".

```
pip install -r requirements.txt
```

Add this app to tardis/settings.py:

```
INSTALLED_APPS += ('tardis.apps.mydata',)
```
Restart MyTardis.

Create Uploader data models:

```
python mytardis.py migrate mydata
```
Restart MyTardis.

Create the `http://mytardis.org/schemas/mydata/defaultexperiment` schema from the fixture provided:

```
python mytardis.py loaddata tardis/apps/mydata/fixtures/default_experiment_schema.json
```

Check that the `http://mytardis.org/schemas/mydata/defaultexperiment` schema is accessible in the Django Admin interface.

Check that the "mytardis-app-mydata" app's API endpoints are accessible.
You should see some API URIs beginning with the "mydata_" prefix in
http://<your-mytardis-host>/api/v1/?format=json

