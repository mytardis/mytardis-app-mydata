# mytardis-app-mydata
Server-side functionality and data models for MyData

UNDER CONSTRUCTION

Run pip to install extra Python module dependencies (django-ipware):

pip install -r requirements.txt

Add this app to tardis/settings.py:

```
INSTALLED_APPS += ('tardis.apps.mydata',)
```

Create Uploader data models:

python mytardis.py syncdb

Create experimentInstrument schema from fixture:

python mytardis.py loaddata tardis/apps/mydata/fixtures/default_experiment_schema.json

