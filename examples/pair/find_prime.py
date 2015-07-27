"""
This example demonstrates how Python code can be run in NodeJS, which
is for many things faster than CPython. We run the exact same code to
find the n-th prime on both Python and JS and measure the performance.
"""

from time import perf_counter
from flexx.pyscript import js
from flexx import pair


def _find_prime(self, n):
    """ The code that is executed on both Python and JS (via PyScript)
    """
    primes = []
    
    def isprime(x):
        if x <= 1:
            return False
        elif x == 2:
            return True
        for i in range(2, x//2+1):
            if x % i == 0:
                return False
        return True
    
    t0 = perf_counter()
    i = 0
    while len(primes) < n:
        i += 1
        if isprime(i):
            primes.append(i)
    t1 = perf_counter()
    print(i, 'found in ', t1-t0, 'seconds')


@pair.app
class PrimeFinder(pair.Pair):
    
    _find_prime = _find_prime
    
    def find_prime_py(self, n):
        self._find_prime(n)
    
    class JS:
        _find_prime = _find_prime
        
    def find_prime_js(self, n):
        self.call_js('_find_prime(%i)' % n)


# Create app instance
finder = PrimeFinder.launch('nodejs')

finder.find_prime_py(2000)  # 0.7 s
finder.find_prime_js(2000)  # 0.2 s

pair.run()