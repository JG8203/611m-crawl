#!/bin/bash

# --- Configuration ---
# Edit these variables to match your testing needs.

# A list of thread counts to test
THREAD_LIST=(1 2 4 8 16)

# Number of times to run the test for EACH thread count
RUNS_PER_SETTING=3

# Duration for each test run (in minutes).
# WARNING: 5 minutes is good for the paper, but will take a long time to run.
# For a quick test of the script, set this to 0.25 (15 seconds).
# For your final paper, set this to 5 or 10.
DURATION_MINUTES=2

# The starting URL
START_URL="http://www.dlsu.edu.ph"

# --- Script ---
RESULTS_DIR="test_results"
SUMMARY_FILE="results_summary.csv"

echo "Starting performance test..."

# Create the results directory if it doesn't exist
mkdir -p $RESULTS_DIR
echo "Saving all logs and output files to: $RESULTS_DIR"

# Clear any old summary file and write the CSV header
rm -f $SUMMARY_FILE
echo "thread_count,run,pages_visited,pages_discovered,links_found" > $SUMMARY_FILE
echo "Writing summary to: $SUMMARY_FILE"
echo ""
echo "!!! WARNING: Test duration is set to $DURATION_MINUTES minutes per run."
echo "!!! Edit this script and change DURATION_MINUTES to 5 or 10 for your final paper."
echo ""

# Loop over each thread count
for threads in "${THREAD_LIST[@]}"; do
  echo "----------------------------------------"
  echo "Testing with $threads thread(s)..."

  # Loop for the number of runs
  for (( run=1; run<=$RUNS_PER_SETTING; run++ )); do
    echo "  Running test $run/$RUNS_PER_SETTING..."

    # Define unique filenames for this run's output
    LOG_PREFIX="${RESULTS_DIR}/n${threads}_run${run}"
    METADATA_FILE="${LOG_PREFIX}_metadata.txt"
    CSV_FILE="${LOG_PREFIX}_crawled_urls.csv"
    PYTHON_LOG="${LOG_PREFIX}_stdout.log"

    # Run the python script using poetry and redirect all its print() output to a log file
    poetry run python main.py -n $threads -t $DURATION_MINUTES -u $START_URL > $PYTHON_LOG 2>&1

    # Check if the script produced metadata (it might fail on run 1)
    if [ ! -f "metadata.txt" ]; then
        echo "    ERROR: metadata.txt was not created. Check ${PYTHON_LOG} for errors."
        continue
    fi

    # Move the generated files to the results folder with unique names
    mv metadata.txt "$METADATA_FILE"
    mv crawled_urls.csv "$CSV_FILE"

    # Extract results from the metadata file
    # grep 'Pattern' file | awk '{print $4}' -> finds the line and prints the 4th word
    pages_visited=$(grep "Total pages visited:" "$METADATA_FILE" | awk '{print $4}')
    pages_discovered=$(grep "Total pages discovered:" "$METADATA_FILE" | awk '{print $4}')
    links_found=$(grep "Total links found:" "$METADATA_FILE" | awk '{print $4}')

    # Set to 0 if grep failed to find the line (e.g., script error)
    pages_visited=${pages_visited:-0}
    pages_discovered=${pages_discovered:-0}
    links_found=${links_found:-0}

    echo "    Done. Pages Visited: $pages_visited"

    # Append the results to the summary CSV file
    echo "$threads,$run,$pages_visited,$pages_discovered,$links_found" >> $SUMMARY_FILE

  done
done

echo "----------------------------------------"
echo "All tests complete."
echo ""
echo "Summary of results written to $SUMMARY_FILE:"
echo ""

# Print the final CSV file to the console
cat $SUMMARY_FILE
