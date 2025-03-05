# Parallelized Coach for Splendor Alpha Zero

This implementation adds parallelization to the Coach class to significantly speed up the self-play process during training.

## Implementation Details

The parallelization was implemented using Python's `concurrent.futures.ProcessPoolExecutor`, which allows running multiple self-play games concurrently across multiple CPU cores.

Key changes:

1. Added a worker function `_execute_one_game_worker` that wraps the original `execute_one_game` method
2. Modified `learn_one_iteration` to use a process pool instead of a sequential loop
3. Added configuration options to control the number of worker processes
4. Fixed arena results handling to properly track neural network performance

## Configuration

The number of worker processes can be configured in two ways:

1. By setting `numWorkers` in the args dictionary passed to Coach
2. If not provided, it defaults to `min(numEps, os.cpu_count())`

## Testing

A test script is included to verify the parallelization:

```bash
python test_parallel_coach.py --workers 4 --games 8
```

The script runs a specified number of self-play games in parallel and reports the execution time.

## Performance Considerations

When using parallelization, consider the following:

1. Each worker process creates a separate instance of the game and neural network, which increases memory usage
2. For optimal performance, set `numWorkers` based on your system's CPU core count and available memory
3. The speedup is generally linear with the number of cores, but overhead increases with more processes

## Limitations

1. Logging from parallel processes may not be perfectly synchronized
2. Each process has its own PRNG state, which may affect reproducibility compared to sequential execution

## Usage

No changes are needed to existing code that uses Coach. The parallelization happens automatically. 