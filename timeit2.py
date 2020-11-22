a = [1,2,3,4]
def orig(a):
    return sum(i*inv for i,inv in enumerate(a, 1))


def f(a):
    return a[0]-1 + sum(i*inv for i,inv in enumerate(a[1:], 2))
def g(a):
    return x**4
def h(a):
    return x**8

import timeit
print(timeit.timeit('[orig(a)]', globals=globals()))
print(timeit.timeit('[f(a)]', globals=globals()))
# print(timeit.timeit('[g(a)]', globals=globals()))
# print(timeit.timeit('[h(a)]', globals=globals()))


# def f(x):
#     return x**2
# def g(x):
#     return x**4
# def h(x):
#     return x**8
#
# import timeit
# print(timeit.timeit('[f(42)]', globals=globals()))
# print(timeit.timeit('[g(42)]', globals=globals()))
# print(timeit.timeit('[h(42)]', globals=globals()))