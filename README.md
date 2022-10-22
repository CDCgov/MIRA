
---
output:
  html_document:
      keep_md: yes
---

<!-- README.md is generated from README.Rmd. Please edit that file -->



## Dockerize Irma-Spy (Development Version)

This version allows you to mount the code base that is needed to develop the `irma-spy` dashboard. Any updates or changes to the code will automatically reflects the changes inside the Docker container. This allows continuous integration (CI) of the application.

### Requirements

- Docker version >= 18
- Git version >= 2.21.0

### (1) Clone this respitory

```
git clone https://git.biotech.cdc.gov/nbx0/irma-spy.git
``` 

### (2) CD to `irma-spy` folder where `Dockerfile` file is stored and build the docker image. 

__NOTE:__ `Dockerfile` contains a list of instructions and steps of how to build and run the `irma-spy` dashboard.

```
docker build -t irma-spy-dev:v1.0.0 --target dev .
```

**-t**: add a tag to an image such as the version of the application, e.g. *irma-spy-dev:v1.0.0* or *irma-spy-dev:latest* <br>
**`--`target**: set the target build stage for the docker image. In this case, we want to build the **development** stage. <br>

_The image took approximately < 5 mins to build_

### (3) After the build is completed, you can check if the image is built successfully

```
docker images

REPOSITORY        TAG        IMAGE ID        CREATED        SIZE
irma-spy-dev      v1.0.0     2c22887402d3    2 hours ago    1.49GB
```

### (4) To run the `irma-spy-dev` container

```    
docker run -v /path/to/irma-spy:/irma-spy -d -p 8080:8050 --name irma-spy-dev irma-spy-dev:v1.0.0 
```

**NOTE:** Change __/path/to/irma-spy__ to your local `irma-spy` directory. This directory must contain all of the code base and data files needed to build the `irma-spy` dashboard

**-d**: run the container in detached mode <br>
**-v**: mount code base and data files from host directory to container directory **[host_div]:[container_dir]**. By exposing the host directory to docker container, docker will be able to access data files within that mounted directory and use it to fire up the `irma-spy` dashboard.  <br>
**-p**: map the host port to the container port and then all the requests that are made to the host port will be redirected to the Docker container **[host_port]:[container_port]** <br>
**`--`name**: give an identity to the container <br>

For more information about the Docker syntax, see [Docker run reference](https://docs.docker.com/engine/reference/run/)

#### (5) To check if the container is built sucessfully

```
docker container ps


CONTAINER ID   IMAGE                   COMMAND                  CREATED        STATUS        PORTS                    NAMES
b37b6b19c4e8   irma-spy-dev:v1.0.0     "/bin/bash irma-spy.…"   5 hours ago    Up 5 hours    0.0.0.0:8080->8050/tcp   irma-spy-dev

```

**NOTE:** Here the `irma-spy-dev` container is published on port **8080** on the host machine, and **8050** is the port of where the `irma-spy` is published inside the container.

### (6) Access the `irma-spy` dashboard on the host network

You can visit the local host using your preferred web browser, type in http://localhost:8080, and check if the dashboard is indeed hosted there.


## Dockerize Irma-Spy (Production Version)

This version **ONLY** allows you to mount the data files that are needed to feed into the `irma-spy` dashboard. You do not have access to the code base of `irma-spy` which can ultimately break the program.

### (1) Clone this respitory

```
git clone https://git.biotech.cdc.gov/nbx0/irma-spy.git
``` 

### (2) CD to `irma-spy` folder where `Dockerfile` file is stored and build the docker image. 

```
docker build -t irma-spy-prod:v1.0.0 --target prod .
```

**-t**: add a tag to an image such as the version of the application, e.g. *irma-spy-prod:v1.0.0* or *irma-spy-prod:latest* <br>
**`--`target**: set the target build stage for the docker image. In this case, we want to build the **production** stage. <br>

_The image took approximately < 5 mins to build_

### (3) After the build is completed, you can check if the image is built successfully.

```
docker images

REPOSITORY        TAG        IMAGE ID        CREATED        SIZE
irma-spy-prod     v1.0.0     6dab1b639b9a    2 hours ago    1.49GB
```

### (4) To run the `irma-spy-prod` container

```    
docker run -v /path/to/data:/irma-spy-container -d -p 8050:8050 --name irma-spy-prod irma-spy-prod:v1.0.0 
```

**NOTE:** Change __/path/to/data__ to path of where you store all of the data files needed to feed into `irma-spy` dashboard. This part is a bit different from the **development** version as it does not allow you to access the code base of `irma-spy`. You can only access the `irma-spy-container` directory inside the docker container.

**-d**: run the container in detached mode <br>
**-v**: mount code base and data files from host directory to container directory **[host_div]:[container_dir]**. By exposing the host directory to docker container, docker will be able to access data files within that mounted directory and use it to feed to the `irma-spy` dashboard. <br>
**-p**: map the host port to the container port and then all the requests that are made to the host port will be redirected to the Docker container **[host_port]:[container_port]** <br>
**`--`name**: give a identity to the container <br>

For more information about the Docker syntax, see [Docker run reference](https://docs.docker.com/engine/reference/run/)

#### (5) To check if the container is built sucessfully

```
docker container ps


CONTAINER ID   IMAGE                   COMMAND                  CREATED        STATUS        PORTS                    NAMES
b37b6b19c4e8   irma-spy-dev:v1.0.0     "/bin/bash irma-spy.…"   5 hours ago    Up 5 hours    0.0.0.0:8050->8050/tcp   irma-spy-prod

```

**NOTE:** Here we are publishing the `irma-spy-prod` container on port **8050** on the host machine. This port is different from the **development** version which we previously launched on port **8080**.

### (6) Access the `irma-spy` dashboard on the host network

You can visit the local host using your preferred web browser, type in http://localhost:8050, and check if the dashboard is indeed hosted there.

<br>

Any questions or issues? Please report them on our [github issues](https://git.biotech.cdc.gov/nbx0/irma-spy/-/issues)

<br>


