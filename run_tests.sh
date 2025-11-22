#!/bin/bash

# Test configuration
WORKER_COUNTS=(1 2 4 8 16)
NUM_TRIALS=3
CRAWL_MINUTES=2
RESULTS_DIR="test_results"

# Create results directory
mkdir -p "$RESULTS_DIR"

# Build images first
echo "Building Docker images..."
docker compose build

# Run trials
for TRIAL in $(seq 1 $NUM_TRIALS); do
    echo ""
    echo "##############################################"
    echo "# TRIAL $TRIAL of $NUM_TRIALS"
    echo "##############################################"

    TRIAL_DIR="$RESULTS_DIR/trial_$TRIAL"
    mkdir -p "$TRIAL_DIR"

    # Run tests for each worker count
    for NUM_WORKERS in "${WORKER_COUNTS[@]}"; do
        echo ""
        echo "=============================================="
        echo "Trial $TRIAL: Testing with $NUM_WORKERS worker(s)"
        echo "=============================================="

        # Create output directory for this test
        TEST_OUTPUT_DIR="$TRIAL_DIR/${NUM_WORKERS}_workers"
        mkdir -p "$TEST_OUTPUT_DIR"

        # Clean up any existing containers and output
        docker compose down --remove-orphans 2>/dev/null
        rm -rf output/*

        # Run with specified number of workers
        echo "Starting coordinator + $NUM_WORKERS worker(s) for $CRAWL_MINUTES minutes..."
        CRAWL_MINUTES=$CRAWL_MINUTES docker compose up --scale worker=$NUM_WORKERS --abort-on-container-exit

        # Copy results to trial directory
        if [ -d "output" ] && [ "$(ls -A output 2>/dev/null)" ]; then
            cp output/* "$TEST_OUTPUT_DIR/" 2>/dev/null || true
        fi

        # Clean up
        docker compose down --remove-orphans

        echo "Completed Trial $TRIAL with $NUM_WORKERS worker(s)"
        echo ""

        # Brief pause between tests
        sleep 5
    done
done

echo ""
echo "##############################################"
echo "# ALL TESTS COMPLETED!"
echo "# Results saved in $RESULTS_DIR/"
echo "##############################################"

# Print summary
echo ""
echo "Summary:"
for TRIAL in $(seq 1 $NUM_TRIALS); do
    echo ""
    echo "=== TRIAL $TRIAL ==="
    for NUM_WORKERS in "${WORKER_COUNTS[@]}"; do
        METADATA_FILE="$RESULTS_DIR/trial_$TRIAL/${NUM_WORKERS}_workers/metadata.txt"
        if [ -f "$METADATA_FILE" ]; then
            echo "--- $NUM_WORKERS worker(s) ---"
            head -3 "$METADATA_FILE"
        fi
    done
done
