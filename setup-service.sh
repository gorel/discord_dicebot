#!/bin/bash

# First copy the compose template to systemd
ln -nsf "$(realpath ./compose/docker-compose@.service)" /etc/systemd/system/docker-compose@.service
# Then copy our docker-compose to the directory with compose files
ln -nsf "$(realpath .)" /etc/docker/compose/dicebot
#ln -nsf "$(realpath ./docker-compose.yml)" /etc/docker/compose/dicebot
# And start the docker-compose service
systemctl start docker-compose@dicebot
