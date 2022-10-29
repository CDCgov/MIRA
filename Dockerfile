############# Build Stage: Development ##################

# Get python docker image
FROM python:3.7.6 as dev

# Create working directory variable
ENV WORKDIR=/irma-spy

# Set up volume directory in docker
VOLUME ${WORKDIR}

# Set up working directory in docker
WORKDIR ${WORKDIR}

# Define a system argument
ARG DEBIAN_FRONTEND=noninteractive

# Install system libraries of general use
# Install system libraries of general use
RUN apt-get update && apt-get install -y --no-install-recommends build-essential \
    wget \
    dos2unix

# Copy python requirements file to docker images
COPY external_package_links.txt /irma-spy/external_package_links.txt

# Copy python requirements file to docker images
COPY install_external_packages.sh /irma-spy/install_external_packages.sh

# Allow permission to excute the bash scripts
RUN chmod a+x /irma-spy/install_external_packages.sh

# excute bash script to wget the files and build the packages
CMD ["/bin/bash", "/irma-spy/install_external_packages.sh"]

# Copy python requirements file to docker images
COPY requirements.txt ${WORKDIR}/requirements.txt

# Install python requirements
RUN pip install --no-cache-dir -r ${WORKDIR}/requirements.txt

# Copy python requirements file to docker images
COPY irma-spy.sh ${WORKDIR}/irma-spy.sh

# Convert irma-spy.sh from Windows style line endings to Unix-like control characters
RUN dos2unix ${WORKDIR}/irma-spy.sh

# Allow permission to excute the bash scripts
RUN chmod a+x ${WORKDIR}/irma-spy.sh

# Allow permission to read, write, and execute files in irma-spy directory
RUN chmod -R a+rw ${WORKDIR}

# Make the app available at port 8050
EXPOSE 8050

# Clean up
RUN apt-get autoremove -y && apt-get clean -y && rm -rf /var/lib/apt/lists/*

# Execute the pipeline 
ENTRYPOINT ["/bin/bash", "irma-spy.sh", "dev"]

############# Build Stage: Production ##################

# Get python docker image
FROM python:3.7.6 as prod

# Create working directory variable
ENV WORKDIR=/irma-spy-container

# Set up volume directory in docker
VOLUME ${WORKDIR}

# Set up working directory in docker
WORKDIR ${WORKDIR}

# Define a system argument
ARG DEBIAN_FRONTEND=noninteractive

# Install system libraries of general use
RUN apt-get update && apt-get install -y --no-install-recommends build-essential \
    wget \
    dos2unix

# Copy python requirements file to docker images
COPY external_package_links.txt /irma-spy/external_package_links.txt

# Copy python requirements file to docker images
COPY install_external_packages.sh /irma-spy/install_external_packages.sh

# Allow permission to excute the bash scripts
RUN chmod a+x /irma-spy/install_external_packages.sh

# Excute bash script to wget the files and build the packages
CMD ["/bin/bash", "/irma-spy/install_external_packages.sh"]

# Copy python requirements file to docker images
COPY requirements.txt /irma-spy/requirements.txt

# Install python requirements
RUN pip install --no-cache-dir -r /irma-spy/requirements.txt

# Copy all files to docker images
COPY . /irma-spy/

# Copy execute files to launch irma-spy to docker images
COPY irma-spy.sh /irma-spy/irma-spy.sh

# Convert irma-spy.sh from Windows style line endings to Unix-like control characters
RUN dos2unix /irma-spy/irma-spy.sh

# Allow permission to excute the bash scripts
RUN chmod a+x /irma-spy/irma-spy.sh

# Allow permission to read, write, and execute files in irma-spy directory
RUN chmod -R a+rw /irma-spy

# Allow permission to read, write, and execute files in irma-spy directory
RUN chmod -R a+rw ${WORKDIR}

# Make the app available at port 8050
EXPOSE 8050

# Clean up
RUN apt-get autoremove -y && apt-get clean -y && rm -rf /var/lib/apt/lists/*

# Execute the pipeline 
ENTRYPOINT ["/bin/bash", "/irma-spy/irma-spy.sh", "prod"]






