#!/usr/bin/env python3

print("Quick Open test: exception traceback")


def func4():
    raise ValueError("This is an exception")


def func2():
    func3()


def func1():
    func2()


if __name__ == "__main__":
    func1()
