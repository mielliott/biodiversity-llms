import os
import sys
import pandas as pd

args = iter(sys.argv[1:])

GROUP_BY = str(next(args))
MIN_GROUP_SIZE = int(next(args))
MAX_GROUP_SIZE = int(next(args))
RANDOM_SEED = int(next(args))

try:
    (pd.read_csv(sys.stdin, sep="\t")
        .sample(frac=1, random_state=RANDOM_SEED)
        .groupby([GROUP_BY])
        .filter(lambda group: len(group) > MIN_GROUP_SIZE)
        .groupby([GROUP_BY])  # Is there a better way to chain filter & head?
        .head(MAX_GROUP_SIZE)
        .sort_values(GROUP_BY)
        .to_csv(sys.stdout, sep="\t", index=False))
except BrokenPipeError:
    # Python prints a warning even if the error is caught. This silences the warning.
    devnull = os.open(os.devnull, os.O_WRONLY)
    os.dup2(devnull, sys.stdout.fileno())
    sys.exit(0)
