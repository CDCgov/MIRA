#!/usr/bin/bash

echo -e "\n\n\tYour individual sequencing runs must be saved inside ${PWD}\n\
    \tEnter \"yes\" to confirm.\n\n\
    \tEnter anything else to change the folder to save your\n\
    \tindividual sequencing run folders into and change directory (cd) \
    \n\tinto that folder and rerun this script.\n\n"

read RESPONSE

[ ${RESPONSE,,} != "yes" ] && exit

DC_FILE_CONTENT="version: \"3.9\"\n\
\n\
x-dais-version:\n\
  &dais-version \n\
  public.ecr.aws/n3z8t4o2/dais-ribosome:1.2.1\n\
\n\
x-irma-version:\n\
  &irma-version \n\
  public.ecr.aws/n3z8t4o2/irma:1.0.2p3\n\
\n\
x-spyne-git-version:\n\
  &spyne-git-version  \n\
  https://github.com/nbx0/spyne.git#prod\n\
\n\
x-ispy-git-version:\n\
  &ispy-git-version  \n\
  https://github.com/nbx0/iSpy.git#prod \n\
\n\
x-data-volumes:\n\
  &data-volume\n\
  type: bind\n\
  source: ${PWD}\n\
  target: /data\n\
\n\
x-docker-volumes:\n\
  &docker-socket\n\
  type: bind\n\
  source: /var/run/docker.sock \n\
  target: /var/run/docker.sock \n\
\n\
services:\n\
  dais: \n\
    container_name: dais\n\
    image: *dais-version\n\
    networks:\n\
      - backend\n\
    volumes: \n\
      - *data-volume\n\
    command: tail -f /dev/null\n\
\n\
  irma: \n\
    container_name: irma\n\
    image: *irma-version\n\
    restart: always\n\
    networks:\n\
      - backend\n\
    volumes:\n\
      - *data-volume\n\
    command: tail -f /dev/null\n\
\n\
  spyne: \n\
    container_name: spyne\n\
    image: spyne\n\
    build: \n\
      context: *spyne-git-version \n\
    depends_on:\n\
      - dais\n\
      - irma\n\
    restart: always\n\
    networks:\n\
      - backend\n\
    volumes:\n\
      - *data-volume\n\
      - *docker-socket\n\
    command: tail -f /dev/null\n\
\n\
  ispy: \n\
    container_name: ispy\n\
    image: ispy\n\
    build: \n\
      context: *ispy-git-version  \n\
    depends_on:\n\
      - dais\n\
      - irma\n\
      - spyne\n\
    restart: always\n\
    networks:\n\
      - frontend\n\
      - backend\n\
    ports: \n\
      - 8020:8050\n\
    volumes:\n\
      - *data-volume\n\
      - *docker-socket\n\
\n\
networks:\n\
  backend:\n\
    name: backend\n\
  frontend:\n\
    name: frontend\n"

echo -e "${DC_FILE_CONTENT}" > docker-compose-git.yml

DC_DOWN_CMD="docker-compose \
    -f docker-compose-git.yml \
    down \
        --rmi all \
        -v \
        --remove-orphans"

DC_UP_CMD="docker-compose \
    -f docker-compose-git.yml \
    up \
        -d \
        --always-recreate-deps \
        --pull always \
        --timestamps"

eval $DC_DOWN_CMD
eval $DC_UP_CMD