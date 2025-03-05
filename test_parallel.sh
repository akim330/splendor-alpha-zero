#!/bin/bash

# Test with different worker counts
echo "Testing with default worker count (auto-detection)"
python test_parallel_coach.py --games 8

echo -e "\nTesting with 1 worker (sequential)"
python test_parallel_coach.py --workers 1 --games 8

echo -e "\nTesting with 2 workers"
python test_parallel_coach.py --workers 2 --games 8

echo -e "\nTesting with 4 workers"
python test_parallel_coach.py --workers 4 --games 8

echo -e "\nTesting with 8 workers"
python test_parallel_coach.py --workers 8 --games 8 