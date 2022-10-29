
#!/bin/bash
# Wrapper to launch irma-spy dashboard

RESOURCE_ROOT=/irma-spy
[ $1 == 'dev' ] && YAML="container-dev.yaml" || YAML="container-prod.yaml"
python $RESOURCE_ROOT/app.py $RESOURCE_ROOT/config/$YAML 