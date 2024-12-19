def convert_snake_case_to_hyphens(arg_name: str):
    return arg_name.replace("_", "-")


def convert_args_dict_to_cli(args: dict):
    if not isinstance(args, dict):
        raise RuntimeError("Command args must be a dict. Not this:", args)

    return " ".join(
        f'--{convert_snake_case_to_hyphens(arg)} "{value}"'.lower()
        for arg, value in args.items()
    )
