#!/usr/bin/env bash
set -euo pipefail

RG=AzureLLMLaboratoryRG
LOC=eastus2
FOUNDRY=foundry-llm-mcp

# Uncomment in case you don't have the resource group yet.
# az group create --name $RG --location $LOC

# The Foundry resource is an Azure AI Services account of kind AIServices
az cognitiveservices account create \
    -g $RG -n $FOUNDRY -l $LOC \
    --kind AIServices \
    --sku S0 \
    --custom-domain $FOUNDRY \
    --assign-identity

# --custom-domain is not optional in practice — without it you get a regional shared endpoint that doesn't support Entra ID token auth

