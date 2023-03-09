"""
Checking whether PR author is admin or not
"""

from tap import Tap


class ArgumentParser(Tap):
    """
    Types for the argument parser
    """
    pr_name: str


def main() -> None:
    """
    Entrypoint for checking if PR has skip in name
    """
    args = ArgumentParser().parse_args()

    if '[skip-lab]' in args.pr_name:
        print('YES')
    else:
        print('NO')


if __name__ == '__main__':
    main()
