
#!/bin/bash
# Wrapper to download packages from the web

RESOURCE_ROOT=/irma-spy
external_package_orig=${RESOURCE_ROOT}/external_package_links.txt
external_package_clean=${RESOURCE_ROOT}/external_package_links_clean.txt

if [[ -f ${external_package_orig} ]]
then
	
	# Remove blank lines from the file and save a cleaner version of it
	awk NF < ${external_package_orig} > ${external_package_clean}

	# wget the file and install the package
	cat ${external_package_clean} | awk '{ print $0 }' | wget -i - -q -O ${RESOURCE_ROOT}/fetched_package.tar.gz | tar -zxf ${RESOURCE_ROOT}/fetched_package.tar.gz

fi
