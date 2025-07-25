#!/bin/bash

set -e  # Exit immediately if a command exits with a non-zero status

echo "🔧 Updating package list..."
sudo apt-get update

echo "🔐 Installing dependencies..."
sudo apt-get install -y apt-transport-https ca-certificates gnupg curl

echo "🗝️ Importing Google Cloud public key..."
curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | sudo gpg --dearmor -o /usr/share/keyrings/cloud.google.gpg

echo "📦 Adding Google Cloud CLI repo..."
echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" \
  | sudo tee /etc/apt/sources.list.d/google-cloud-sdk.list

echo "🔁 Updating repo list..."
sudo apt-get update && sudo apt-get install google-cloud-cli

