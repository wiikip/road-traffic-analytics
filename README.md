# road-traffic-analytics

Road Traffic Analytics App

## Build

To build and deploy our application, we use Ansible.

### Requirements:

To deploy the application, the target machine needs to have:
Python3, sha256sum, docker

### Launch

First, fill the vault files in the group_vars directory
Command to launch:
`ansible-playbook -i ansible/inventory ansible/playbook-deploy.yml`

### What Ansible does

Our Ansible repo does 2 main actions. It launches the docker-compose which starts all services, then it configures the services (data sources, connections, etc.).

**Docker-compose**
Most of the services are contained in the `docker-compose.yml` file.

**Cron**
Once the services are up, Ansible launches a cron job (`cron.py`). This service fetches the bikes and cars records on [Paris' OpenData plateform](https://opendata.paris.fr/explore/dataset/comptage-velo-donnees-compteurs/information/?disjunctive.id_compteur&disjunctive.nom_compteur&disjunctive.id&disjunctive.name) and simulates a real-time flow of cars and bikes that pass in front of the counters.

**Druid**
Ansible configures Druid. It creates datasources, then it sets up a new user (called Superset) with read-only rights.

**SuperSet**
Ansible connects SuperSet to Druid using the previously created user. Then it imports our dashboard on SuperSet.

## Fonctionnement

schéma d’archi

- description des services ?
  Cron pour le tps réel
