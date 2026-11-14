#!/usr/bin/env bash
set -euo pipefail

RG=AzureLLMLaboratoryRG
FOUNDRY=foundry-llm-mcp

az cognitiveservices model list -l $LOC \
  --query "[?model.name=='gpt-4.1-nano'].{name:model.name, version:model.version, sku:model.skus[0].name}" \
  -o table

az cognitiveservices account deployment create \
  -g $RG -n $FOUNDRY \
  --deployment-name kpi-router \
  --model-name gpt-4.1-nano \
  --model-version "2025-04-14" \
  --model-format OpenAI \
  --sku-name GlobalStandard \
  --sku-capacity 50