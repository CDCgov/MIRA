
# Create a build argument
ARG BUILD_STAGE
ARG BUILD_STAGE=${BUILD_STAGE:-prod}

############# Build Stage: Dependencies ##################

# Start from a base image
FROM python:3.7.6 as base

# Define a system argument
ARG DEBIAN_FRONTEND=noninteractive

# Start from a base image
FROM python:3.7.6 as base

# Define a system argument
ARG DEBIAN_FRONTEND=interactive

# Install system libraries of general use
RUN apt-get update --allow-releaseinfo-change && apt-get install -y --no-install-recommends build-essential \ 
    iptables \
    libdevmapper1.02.1 \
    dpkg \
    sudo \
    wget \
    curl \
    dos2unix

############# Build Stage: Development ##################

# Build from the base image for dev
FROM base as dev

# Create working directory variable
ENV WORKDIR=/irma-spy

# Create a stage enviroment
ENV STAGE=dev

# Create a directory to store data
RUN mkdir /data

# Allow permission to read and write files to data directory
RUN chmod -R a+rwx /data

############# Build Stage: Production ##################

# Build from the base image for prod
FROM base as prod

# Create working directory variable
ENV WORKDIR=/data

# Create a stage enviroment
ENV STAGE=prod

# Copy all scripts to docker images
COPY . /irma-spy

############# Build Stage: Final ##################

# Build the final image 
FROM ${BUILD_STAGE} as final

# Set up volume directory in docker
VOLUME ${WORKDIR}

# Set up working directory in docker
WORKDIR ${WORKDIR}

# Allow permission to read and write files to current working directory
RUN chmod -R a+rw ${WORKDIR}

############# Install Docker ##################

# Copy all files to docker images
COPY docker /irma-spy/docker

# Copy all files to docker images
COPY install_docker.sh /irma-spy/install_docker.sh

# Convert bash script from Windows style line endings to Unix-like control characters
RUN dos2unix /irma-spy/install_docker.sh

# Allow permission to excute the bash script
RUN chmod a+x /irma-spy/install_docker.sh

# Execute bash script to install the package
RUN bash /irma-spy/install_docker.sh

############# Install python packages ##################

# Upgrade pip
CMD python -m pip --upgrade pip

# Copy python requirements file to docker images
COPY requirements.txt /irma-spy/requirements.txt

# Install python requirements
RUN pip install -r /irma-spy/requirements.txt

############# Launch irma-spy dashboard ##################

# Copy all files to docker images
COPY irma-spy.sh /irma-spy/irma-spy.sh

# Convert irma-spy.sh from Windows style line endings to Unix-like control characters
RUN dos2unix /irma-spy/irma-spy.sh

# Allow permission to excute the bash scripts
RUN chmod a+x /irma-spy/irma-spy.sh

# Allow permission to read and write files to irma-spy directory
RUN chmod -R a+rw /irma-spy

# Make the app available at port 8050
EXPOSE 8050

# Clean up
RUN apt-get autoremove -y && apt-get clean -y && rm -rf /var/lib/apt/lists/*

# Execute the pipeline 
ENTRYPOINT ["/bin/bash", "/irma-spy/irma-spy.sh"]

