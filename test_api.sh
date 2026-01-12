#!/usr/bin/env bash
# Quick test script for slicer service

set -euo pipefail

BASE_URL="http://localhost:8080"

echo "Testing slicer service..."

# Test 1: Health check
echo "1. Health check..."
curl -s "$BASE_URL/" | jq .

# Test 2: Create a dummy STL (just a text file for testing API)
echo -e "\n2. Creating dummy STL..."
echo "fake stl content" > /tmp/test.stl

# Test 3: Upload STL
echo -e "\n3. Uploading STL..."
UPLOAD_RESPONSE=$(curl -s -F "file=@/tmp/test.stl" "$BASE_URL/upload-stl")
echo "$UPLOAD_RESPONSE" | jq .
STL_PATH=$(echo "$UPLOAD_RESPONSE" | jq -r .stl_path)

# Test 4: Slice (will fail without real CuraEngine but tests API)
echo -e "\n4. Attempting slice (may fail without CuraEngine)..."
curl -s -X POST "$BASE_URL/slice" \
  -H "Content-Type: application/json" \
  -d "{
    \"stl_path\": \"$STL_PATH\",
    \"printer_id\": \"test_printer\",
    \"material\": \"PLA\",
    \"profile\": \"standard\",
    \"nozzle_size\": 0.4
  }" | jq . || echo "Slice failed (expected without CuraEngine)"

# Test 5: Submit feedback
echo -e "\n5. Submitting feedback..."
curl -s -X POST "$BASE_URL/feedback" \
  -H "Content-Type: application/json" \
  -d '{
    "printer_id": "test_printer",
    "material": "PLA",
    "profile": "standard",
    "profile_version": 1,
    "result": "failure",
    "failure_type": "under_extrusion",
    "quality_rating": 2,
    "notes": "Test feedback"
  }' | jq .

# Test 6: Get profiles
echo -e "\n6. Getting profiles..."
curl -s "$BASE_URL/profiles/test_printer/PLA" | jq .

# Test 7: Get feedback history
echo -e "\n7. Getting feedback history..."
curl -s "$BASE_URL/feedback/test_printer" | jq .

echo -e "\n✅ API tests complete!"
