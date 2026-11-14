#!/usr/bin/env bash
set -euo pipefail

RG=AzureLLMLaboratoryRG
LOC=eastus2
FOUNDRY=foundry-llm-mcp
ACR=acrllmmcp$RANDOM
ENV=cae-llm-mcp

echo "Creating Azure Container Registry $ACR and Container Apps environment $ENV in resource group $RG..."
az acr create -g $RG -n $ACR --sku Basic --admin-enabled true
az containerapp env create -g $RG -n $ENV -l $LOC

# Build mcp-server image
echo "Building mcp-server image..."
az acr build --registry $ACR --image mcp-server:v1 --platform linux/amd64 ./mcp_server

# Build gateway image
echo "Building gateway image..."
az acr build --registry $ACR --image gateway:v1    --platform linux/amd64 ./gateway

# Create container apps for mcp-server
echo "Creating container apps for mcp-server..."
az containerapp create \
  -g $RG -n mcp-server --environment $ENV \
  --image $ACR.azurecr.io/mcp-server:v1 \
  --registry-server $ACR.azurecr.io \
  --target-port 9000 --ingress internal \
  --min-replicas 1 --max-replicas 3 \
  --cpu 0.5 --memory 1Gi

# Create container apps for gateway. 
# Keep --min-replicas 1. 
# The gateway calls list_tools() at startup and will fail outright against a scaled-to-zero MCP app.
echo "Creating container apps for gateway..."
az containerapp create \
  -g $RG -n gateway --environment $ENV \
  --image $ACR.azurecr.io/gateway:v1 \
  --registry-server $ACR.azurecr.io \
  --target-port 8080 --ingress external \
  --min-replicas 1 --max-replicas 10 \
  --cpu 1.0 --memory 2Gi \
  --env-vars \
    AZURE_ENDPOINT=https://$FOUNDRY.openai.azure.com \
    AZURE_DEPLOYMENT=kpi-router \
    AZURE_API_VERSION=2024-10-21 \
    MCP_URL=http://mcp-server:9000/mcp

echo "Assigning managed identity to gateway and granting Cognitive Services OpenAI User role..."
az containerapp identity assign -g $RG -n gateway --system-assigned

PRINCIPAL=$(az containerapp identity show -g $RG -n gateway --query principalId -o tsv)
SCOPE=$(az cognitiveservices account show -g $RG -n $FOUNDRY --query id -o tsv)

az role assignment create \
  --assignee-object-id $PRINCIPAL --assignee-principal-type ServicePrincipal \
  --role "Cognitive Services OpenAI User" \
  --scope $SCOPE

echo "Restarting gateway revision..."
az containerapp revision restart -g $RG -n gateway \
  --revision $(az containerapp revision list -g $RG -n gateway --query "[0].name" -o tsv)