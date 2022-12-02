#!/bin/bash

ln -nsf /etc/systemd/system/docker-compose@.service ./compose/docker-compose@.service
ln -nsf /etc/docker/compose/dicebot ./docker-compose.yml
systemctl start docker-compose@
