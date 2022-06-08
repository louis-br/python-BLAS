# %%
import numpy as np

# %%
a = np.genfromtxt("a.csv", dtype=float, delimiter=";")
aM = np.genfromtxt("aM.csv", dtype=float, delimiter=";")
M = np.genfromtxt("M.csv", dtype=int, delimiter=";")
MN = np.genfromtxt("MN.csv", dtype=int, delimiter=";")
N = np.genfromtxt("N.csv", dtype=int, delimiter=";")


# %%
res = np.matmul(M, N)
print(res)

# %%
print(np.testing.assert_equal(res, MN))

# %%
res = np.matmul(a, M)
print(res)

# %%
print(np.testing.assert_almost_equal(res, aM, decimal=2))