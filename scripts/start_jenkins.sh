#!/usr/bin/env bash
set -euo pipefail

KUBECONFIG_SOURCE="${HOME}/.kube/config"
KUBECONFIG_TMP="$(mktemp /tmp/jenkins-kubeconfig.XXXXXX)"

cp "$KUBECONFIG_SOURCE" "$KUBECONFIG_TMP"
sed -i '' 's#https://127.0.0.1:6443#https://kubernetes.docker.internal:6443#g' "$KUBECONFIG_TMP"

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
  -v "$KUBECONFIG_TMP:/home/jenkins/.kube/config:ro" \
  -e KUBECONFIG=/home/jenkins/.kube/config \
  house-price-jenkins:local
