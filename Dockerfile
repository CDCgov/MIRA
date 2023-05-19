
# Create a build argument
ARG BUILD_STAGE
ARG BUILD_STAGE=${BUILD_STAGE:-prod}

############# Build Stage: Dependencies ##################

# Start from a base image
FROM --platform=linux/amd64 ubuntu:focal as base

# Define a system argument
ARG DEBIAN_FRONTEND=noninteractive

# Install system libraries of general use
RUN apt-get update --allow-releaseinfo-change && apt-get install --no-install-recommends -y \
    build-essential \ 
    iptables \
    libdevmapper1.02.1 \
    libudunits2-dev \
    libv8-dev \
    libsodium-dev \
    libbz2-dev \
    liblzma-dev \
    libsasl2-dev \
    krb5-user \ 
    unixodbc \
    unixodbc-dev \
    dpkg-dev \
    debhelper \    
    python3.8 \
    python3-venv \
    python3-pip \
    python3-setuptools \
    python3-dev \
    dpkg \
    sudo \
    wget \
    curl \
    nano \
    xtail \
    dos2unix

############# Build Stage: Development ##################

# Build from the base image for dev
FROM base as dev

# Create working directory variable
ENV WORKDIR=/data

# Create a stage enviroment
ENV STAGE=dev

############# Build Stage: Production ##################

# Build from the base image for prod
FROM base as prod

# Create working directory variable
ENV WORKDIR=/data

# Create a stage enviroment
ENV STAGE=prod

# Copy all scripts to docker images
COPY . /MIRA

############# Build Stage: Final ##################

# Build the final image 
FROM ${BUILD_STAGE} as final

# Set up volume directory in docker
VOLUME ${WORKDIR}

# Set up working directory in docker
WORKDIR ${WORKDIR}

# Allow permission to read and write files to current working directory
RUN chmod -R a+rwx ${WORKDIR}

############# Install ODBC Driver ##################

# Copy Cloudera Impala ODBC driver (64-bit) to docker images 
COPY odbc/clouderaimpalaodbc_2.6.14.1016-2_amd64.deb /MIRA/odbc/clouderaimpalaodbc_2.6.14.1016-2_amd64.deb

# Install Impala ODBC driver
RUN dpkg -i /MIRA/odbc/clouderaimpalaodbc_2.6.14.1016-2_amd64.deb

# Specify locations of the connector configuration files in docker images 
# 1. odbc.ini (DSN)
# 2. odbcinst.ini (NO DSN)
# 3. cloudera.impalaodbc.ini (connector-wide settings)

ENV ODBCINI=/etc/odbc.ini
ENV ODBCSYSINI=/etc/odbcinst.ini
ENV CLOUDERAIMPALAINI=/opt/cloudera/impalaodbc/lib/64/cloudera.impalaodbc.ini
ENV LD_LIBRARY_PATH=/opt/cloudera/impalaodbc/lib/64

# Copy configuration files to their specified locations in docker images
COPY odbc/odbc.ini $ODBCINI
COPY odbc/odbcinst.ini $ODBCSYSINI
COPY odbc/cloudera.impalaodbc.ini $CLOUDERAIMPALAINI

############# Install GISAID EpiFlu CLI ##################

# Copy all files to docker images
COPY epiflu_cli /MIRA/epiflu_cli

############# Install Docker ##################

# Copy all files to docker images
COPY docker /MIRA/docker

# Copy all files to docker images
COPY install_docker.sh /MIRA/install_docker.sh

# Convert bash script from Windows style line endings to Unix-like control characters
RUN dos2unix /MIRA/install_docker.sh

# Allow permission to excute the bash script
RUN chmod a+x /MIRA/install_docker.sh

# Execute bash script to install the package
RUN bash /MIRA/install_docker.sh

############# Install python packages ##################

# Copy python requirements file to docker images
COPY requirements.txt /MIRA/requirements.txt

# Install python requirements
RUN pip3 install --no-cache-dir -r /MIRA/requirements.txt

############# Launch MIRA dashboard ##################

# Copy all files to docker images
COPY dashboard-kickoff /MIRA/dashboard-kickoff

# Convert bash script from Windows style line endings to Unix-like control characters
RUN dos2unix /MIRA/dashboard-kickoff

# Allow permission to excute the bash scripts
RUN chmod a+x /MIRA/dashboard-kickoff

# Allow permission to read and write files to MIRA directory
RUN chmod -R a+rwx /MIRA

# Make the app available at port 8050
EXPOSE 8050

# Clean up
RUN apt-get autoremove -y && apt-get clean -y && rm -rf /var/lib/apt/lists/*

# Export bash script to path
ENV PATH "$PATH:/MIRA"

# Execute the pipeline 
ENTRYPOINT ["bash", "dashboard-kickoff"]
