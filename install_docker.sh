
#!/bin/bash
# Wrapper to install downloaded packages

RESOURCE_ROOT=/iSpy
docker_file_orig=${RESOURCE_ROOT}/docker/docker_file.txt
docker_file_clean=${RESOURCE_ROOT}/docker/docker_file_clean.txt

if [[ -f ${docker_file_orig} ]]
then

	echo "Install docker"

	# Remove blank lines from the file and save a cleaner version of it
	awk NF < ${docker_file_orig} > ${docker_file_clean}

	# Get number of rows in external_package_links_clean.txt
	n=`wc -l < ${docker_file_clean}`
	i=1

	# Wget the file and install the package
	while [[ i -le $n ]];
	do
		echo $i
		file=$(head -${i} ${docker_file_clean} | tail -1 | sed 's,\r,,g')
		echo $file
		sudo dpkg -i ${RESOURCE_ROOT}/docker/${file}
		i=$(($i+1))
	done

	# return message to keep the process going
	echo "Done"

fi

