#!/usr/bin/env bash
set -euo pipefail

docker build -f docker/jenkins.Dockerfile -t house-price-jenkins:local .

docker rm -f house-price-jenkins >/dev/null 2>&1 || true

docker run -d \
  --name house-price-jenkins \
  --restart unless-stopped \
  --group-add 0 \
  -p 8080:8080 \
  -p 50000:50000 \
  -v jenkins_home:/var/jenkins_home \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v "$HOME/.kube:/home/jenkins/.kube:ro" \
  -e KUBECONFIG=/home/jenkins/.kube/config \
  house-price-jenkins:local
