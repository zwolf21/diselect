import argparse

from sample1 import test_sample1
from sample2 import test_sample2


# Tested in venv for avoiding import errors

def main():
    argparser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter, description='Test For diselect'
    )
    argparser.add_argument('appname', type=str,  help='Input app name for test')

    args = argparser.parse_args()

    if args.appname in ['sample1']:
        test_sample1()

    if args.appname in ['sample2']:
        test_sample2()


if __name__ == '__main__':
    main()