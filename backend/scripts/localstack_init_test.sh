#!/bin/bash

# LocalStack Init — Ambiente de Teste
# Executado automaticamente quando o LocalStack de teste está pronto.
# Cria os recursos mínimos necessários para os testes de integração.


set -e

REGION="us-east-1"
ENDPOINT="http://localhost:4566"
QUEUE_NAME="submissions-corrections"
BUCKET_NAME="submissions-texts"

echo "🧪 [TEST] Initializing LocalStack test resources..."

# SQS: Fila principal
echo "📬 Creating SQS queue: $QUEUE_NAME"
awslocal sqs create-queue \
  --queue-name "$QUEUE_NAME" \
  --region "$REGION" \
  --attributes "VisibilityTimeout=30,MessageRetentionPeriod=3600" \
  > /dev/null

echo "   ✅ Queue created"

# S3: Bucket para textos
echo "🪣 Creating S3 bucket: $BUCKET_NAME"
awslocal s3api create-bucket \
  --bucket "$BUCKET_NAME" \
  --region "$REGION" 2>/dev/null || echo "   ℹ️  Bucket already exists"

echo "   ✅ Bucket created"

# Verificação
echo ""
echo "✅ [TEST] LocalStack ready:"
echo "   SQS: http://localhost:4566/000000000000/$QUEUE_NAME"
echo "   S3:  s3://$BUCKET_NAME"