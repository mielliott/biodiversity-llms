
import sys


def get_config_file_path():
    if "--configfile" in sys.argv:
        i = sys.argv.index("--configfile")
    elif "--configfiles" in sys.argv:
        i = sys.argv.index("--configfiles")

    return sys.argv[i + 1]


def get_job_and_dataset():
    config_path = get_config_file_path()
    dataset = config_path.split("/")[-2]
    job = config_path.split("/")[-1][:-4]

    return job, dataset
