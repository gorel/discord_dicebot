#!/bin/bash

# First copy the compose template to systemd
ln -nsf /etc/systemd/system/docker-compose@.service ./compose/docker-compose@.service
# Then copy our docker-compose to the directory with compose files
ln -nsf /etc/docker/compose/dicebot ./docker-compose.yml
# And start the docker-compose service
systemctl start docker-compose@
