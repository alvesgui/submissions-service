#!/bin/bash

# LocalStack Init Script
# Executado automaticamente quando o LocalStack está pronto.
# Cria os recursos AWS que a aplicação precisa.

set -e

REGION="${DEFAULT_REGION:-us-east-1}"
ENDPOINT="http://localhost:4566"
QUEUE_NAME="${SQS_QUEUE_NAME:-submissions-corrections}"
DLQ_NAME="${SQS_DLQ_NAME:-submissions-corrections-dlq}"
BUCKET_NAME="${S3_BUCKET:-submissions-texts}"

echo "🚀 Initializing LocalStack resources..."
echo "   Region:  $REGION"
echo "   Queue:   $QUEUE_NAME"
echo "   DLQ:     $DLQ_NAME"
echo "   Bucket:  $BUCKET_NAME"

# SQS: Dead Letter Queue
echo "📬 Creating Dead Letter Queue: $DLQ_NAME"
DLQ_URL=$(awslocal sqs create-queue \
  --queue-name "$DLQ_NAME" \
  --region "$REGION" \
  --query 'QueueUrl' \
  --output text)

DLQ_ARN=$(awslocal sqs get-queue-attributes \
  --queue-url "$DLQ_URL" \
  --attribute-names QueueArn \
  --region "$REGION" \
  --query 'Attributes.QueueArn' \
  --output text)

echo "   ✅ DLQ ARN: $DLQ_ARN"

# SQS: Main Queue com Redrive Policy
echo "📬 Creating Main Queue: $QUEUE_NAME"
awslocal sqs create-queue \
  --queue-name "$QUEUE_NAME" \
  --region "$REGION" \
  --attributes "{
    \"VisibilityTimeout\": \"60\",
    \"MessageRetentionPeriod\": \"86400\",
    \"RedrivePolicy\": \"{\\\"deadLetterTargetArn\\\":\\\"$DLQ_ARN\\\",\\\"maxReceiveCount\\\":\\\"3\\\"}\"
  }"

echo "   ✅ Main queue created with redrive policy (maxReceiveCount=3)"

# S3: Bucket para textos das submissões
echo "🪣 Creating S3 bucket: $BUCKET_NAME"
awslocal s3api create-bucket \
  --bucket "$BUCKET_NAME" \
  --region "$REGION" 2>/dev/null || echo "   ℹ️  Bucket already exists"

# Bloqueia acesso público
awslocal s3api put-public-access-block \
  --bucket "$BUCKET_NAME" \
  --public-access-block-configuration \
    "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true"

echo "   ✅ Bucket created with public access blocked"

# Verificação final
echo ""
echo "✅ LocalStack init complete! Resources created:"
echo "   SQS Queue: $(awslocal sqs get-queue-url --queue-name $QUEUE_NAME --region $REGION --query 'QueueUrl' --output text)"
echo "   SQS DLQ:   $(awslocal sqs get-queue-url --queue-name $DLQ_NAME --region $REGION --query 'QueueUrl' --output text)"
echo "   S3 Bucket: s3://$BUCKET_NAME"
