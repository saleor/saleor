from sympy.core.compatibility import range
from sympy import symbols, FiniteSet
from sympy.combinatorics.polyhedron import (Polyhedron,
    tetrahedron, cube as square, octahedron, dodecahedron, icosahedron,
    cube_faces)
from sympy.combinatorics.permutations import Permutation
from sympy.combinatorics.perm_groups import PermutationGroup
from sympy.utilities.pytest import raises

rmul = Permutation.rmul


def test_polyhedron():
    raises(ValueError, lambda: Polyhedron(list('ab'),
        pgroup=[Permutation([0])]))
    pgroup = [Permutation([[0, 7, 2, 5], [6, 1, 4, 3]]),
              Permutation([[0, 7, 1, 6], [5, 2, 4, 3]]),
              Permutation([[3, 6, 0, 5], [4, 1, 7, 2]]),
              Permutation([[7, 4, 5], [1, 3, 0], [2], [6]]),
              Permutation([[1, 3, 2], [7, 6, 5], [4], [0]]),
              Permutation([[4, 7, 6], [2, 0, 3], [1], [5]]),
              Permutation([[1, 2, 0], [4, 5, 6], [3], [7]]),
              Permutation([[4, 2], [0, 6], [3, 7], [1, 5]]),
              Permutation([[3, 5], [7, 1], [2, 6], [0, 4]]),
              Permutation([[2, 5], [1, 6], [0, 4], [3, 7]]),
              Permutation([[4, 3], [7, 0], [5, 1], [6, 2]]),
              Permutation([[4, 1], [0, 5], [6, 2], [7, 3]]),
              Permutation([[7, 2], [3, 6], [0, 4], [1, 5]]),
              Permutation([0, 1, 2, 3, 4, 5, 6, 7])]
    corners = tuple(symbols('A:H'))
    faces = cube_faces
    cube = Polyhedron(corners, faces, pgroup)

    assert cube.edges == FiniteSet(*(
        (0, 1), (6, 7), (1, 2), (5, 6), (0, 3), (2, 3),
        (4, 7), (4, 5), (3, 7), (1, 5), (0, 4), (2, 6)))

    for i in range(3):  # add 180 degree face rotations
        cube.rotate(cube.pgroup[i]**2)

    assert cube.corners == corners

    for i in range(3, 7):  # add 240 degree axial corner rotations
        cube.rotate(cube.pgroup[i]**2)

    assert cube.corners == corners
    cube.rotate(1)
    raises(ValueError, lambda: cube.rotate(Permutation([0, 1])))
    assert cube.corners != corners
    assert cube.array_form == [7, 6, 4, 5, 3, 2, 0, 1]
    assert cube.cyclic_form == [[0, 7, 1, 6], [2, 4, 3, 5]]
    cube.reset()
    assert cube.corners == corners

    def check(h, size, rpt, target):

        assert len(h.faces) + len(h.vertices) - len(h.edges) == 2
        assert h.size == size

        got = set()
        for p in h.pgroup:
            # make sure it restores original
            P = h.copy()
            hit = P.corners
            for i in range(rpt):
                P.rotate(p)
                if P.corners == hit:
                    break
            else:
                print('error in permutation', p.array_form)
            for i in range(rpt):
                P.rotate(p)
                got.add(tuple(P.corners))
                c = P.corners
                f = [[c[i] for i in f] for f in P.faces]
                assert h.faces == Polyhedron(c, f).faces
        assert len(got) == target
        assert PermutationGroup([Permutation(g) for g in got]).is_group

    for h, size, rpt, target in zip(
        (tetrahedron, square, octahedron, dodecahedron, icosahedron),
        (4, 8, 6, 20, 12),
        (3, 4, 4, 5, 5),
            (12, 24, 24, 60, 60)):
        check(h, size, rpt, target)
