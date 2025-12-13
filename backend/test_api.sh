#!/bin/bash

# TTB Label Verification API Test Script
# Usage: ./test_api.sh <image_path>
# Example: ./test_api.sh ../data/sample_label.jpg

BASE_URL="http://127.0.0.1:8000"

echo "=========================================="
echo "TTB Label Verification API Test"
echo "=========================================="
echo ""

# Test 1: Health Check
echo "1. Testing Health Check..."
curl -s "${BASE_URL}/api/health" | python3 -m json.tool
echo ""

# Test 2: Root Endpoint
echo "2. Testing Root Endpoint..."
curl -s "${BASE_URL}/" | python3 -m json.tool
echo ""

# Check if image path is provided
if [ -z "$1" ]; then
    echo "=========================================="
    echo "To test label verification, provide an image:"
    echo "./test_api.sh <path_to_label_image>"
    echo ""
    echo "Example:"
    echo "./test_api.sh ../data/sample_label.jpg"
    echo "=========================================="
    exit 0
fi

IMAGE_PATH="$1"

if [ ! -f "$IMAGE_PATH" ]; then
    echo "Error: Image file not found: $IMAGE_PATH"
    exit 1
fi

echo "=========================================="
echo "3. Testing Label Verification"
echo "   Image: $IMAGE_PATH"
echo "=========================================="
echo ""

# Test 3: Label Verification - Scenario A (matching data)
echo "Scenario A: Testing with matching form data..."
curl -s -X POST "${BASE_URL}/api/verify-label" \
    -F "images=@${IMAGE_PATH}" \
    -F "brand=Old Tom Distillery" \
    -F "type=Kentucky Straight Bourbon Whiskey" \
    -F "abv=45%" \
    -F "volume=750mL" | python3 -m json.tool

echo ""
echo "=========================================="
echo "Tests completed!"
echo "=========================================="

