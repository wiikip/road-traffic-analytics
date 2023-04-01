import requests
import json
import os

superset_base_url = "http://localhost:8088/"

superset_login_url = superset_base_url + "api/v1/security/login"
superset_csrf_url = superset_base_url + "api/v1/security/csrf_token"
superset_database_url = superset_base_url + "api/v1/database/"
superset_dataset_url = superset_base_url + "api/v1/dataset/"

druid_router_base_url = "http://localhost:8888/"
druid_datasources_url = druid_router_base_url + "druid/v2/datasources"

charts_directory = "./charts"
superset_chart_import_url = superset_base_url + "api/v1/chart/import/"

SUPERSET_USER = "admin"
SUPERSET_PASSWORD = os.getenv("SUPERSET_PASSWORD")
SUPERSET_USER_IN_DRUID = os.getenv("SUPERSET_USER_IN_DRUID")
SUPERSET_PASSWORD_IN_DRUID = os.getenv("SUPERSET_PASSWORD_IN_DRUID")
DRUID_PASSWORD = os.getenv("DRUID_PASSWORD")
DRUID_USER = os.getenv("DRUID_USER")

def get_access_token(session):
    login_data = {
      "password": SUPERSET_PASSWORD,
      "provider": "db",
      "refresh": False,
      "username": SUPERSET_USER
    }
    response = session.post(url=superset_login_url, json=login_data)
    response.raise_for_status()
    return json.loads(response.text)['access_token']


def get_crsf_token(session, access_token):
    head = {
        "Authorization": "Bearer " + access_token
    }
    response = session.get(url=superset_csrf_url, headers=head)
    response.raise_for_status()
    return json.loads(response.text)['result']


def create_db_connection(session, access_token, crsf_token):
    sqlalchemy_uri = "druid://{}:{}@broker:8082/druid/v2/sql".format(SUPERSET_USER_IN_DRUID, SUPERSET_PASSWORD_IN_DRUID)
    data_out = {
      "database_name": "Apache druid",
      "expose_in_sqllab": True,
      "sqlalchemy_uri": sqlalchemy_uri
    }
    print(data_out)
    headers = {
        'Referrer': superset_login_url,
        'X-CSRFToken': crsf_token,
        "Authorization": "Bearer " + access_token
    }
    response = session.post(url=superset_database_url, headers=headers, json=data_out)
    response.raise_for_status()
    return json.loads(response.text)['id']


def datasources_created_in_druid():
    druid_session = requests.session()
    druid_session.auth = (DRUID_USER, DRUID_PASSWORD)
    response = druid_session.get(url=druid_datasources_url)
    response.raise_for_status()
    return json.loads(response.text)


def create_dataset(session, access_token, crsf_token, database_id, dataset_name):
    data_out = {
        "database": database_id,
        "schema": "druid",
        "table_name": dataset_name
    }
    headers = {
        'Referrer': superset_login_url,
        'X-CSRFToken': crsf_token,
        "Authorization": "Bearer " + access_token
    }
    response = session.post(url=superset_dataset_url, headers=headers, json=data_out)
    response.raise_for_status()
    return json.loads(response.text)['id']


def wait_druid_datasources_to_create_datasets(superset_session, access_token, crsf_token, database_id):
    car_dataset_created = False
    bike_dataset_created = False
    while not car_dataset_created or not bike_dataset_created:
        druid_datasources = datasources_created_in_druid()
        if not car_dataset_created and 'car' in druid_datasources:
            car_dataset_id = create_dataset(superset_session, access_token, crsf_token, database_id, "car")
            print("Superset car dataset created with id", car_dataset_id)
            car_dataset_created = True
        if not bike_dataset_created and 'bike' in druid_datasources:
            bike_dataset_id = create_dataset(superset_session, access_token, crsf_token, database_id, "bike")
            print("Superset bike dataset created with id", bike_dataset_id)
            bike_dataset_created = True


def import_charts(superset_session, access_token, crsf_token):
    for filename in os.listdir(charts_directory):
        f = os.path.join(charts_directory, filename)
        if f.split('.')[-1] == 'zip':
            print("Importing export file ", f, "...")
            data_out = {
                "overwrite": "true",
                "passwords": json.dumps({"databases/Apache_druid.yaml": SUPERSET_PASSWORD_IN_DRUID})
            }
            files = {
                'formData': ( filename, open(f, 'rb'), 'application/json')
            }
            headers = {
                'Referrer': superset_login_url,
                'X-CSRFToken': crsf_token,
                "Authorization": "Bearer " + access_token,
                'accept': 'application/json'
            }
            response = superset_session.post(url=superset_chart_import_url, headers=headers, files=files, data=data_out)
            response.raise_for_status()
            if json.loads(response.text)["message"] == "OK":
                print("Export file ", f, " successfully imported")


def deploy_superset():
    print("Defined env vars: SUPERSET_USER ", SUPERSET_USER, " SUPERSET_PASSWORD ", SUPERSET_PASSWORD, " SUPERSET_USER_IN_DRUID ", SUPERSET_USER_IN_DRUID, " SUPERSET_PASSWORD_IN_DRUID ", SUPERSET_PASSWORD_IN_DRUID, " DRUID_USER ", DRUID_USER, " DRUID_PASSWORD ", DRUID_PASSWORD)
    superset_session = requests.session()
    access_token = get_access_token(superset_session)
    crsf_token = get_crsf_token(superset_session, access_token)

    database_id = create_db_connection(superset_session, access_token, crsf_token)
    print("Superset database created with id", database_id)
    
    wait_druid_datasources_to_create_datasets(superset_session, access_token, crsf_token, database_id)

    print("Import charts")
    import_charts(superset_session, access_token, crsf_token)


if __name__ == "__main__":
    deploy_superset()