class Solution(object):
    def rangeAddQueries(self, n, queries):
        """
        :type n: int
        :type queries: List[List[int]]
        :rtype: List[List[int]]
        """
        def applyQuery(start: tuple, end: tuple, mat: list[list[int]]) -> list[list[int]]:
            for dx in range(start[0], end[0] + 1, 1):
                for dy in range(start[1], end[1] + 1, 1):
                    mat[dy][dx] += 1
            return mat

        mat = [[0 for i in range(n)] for i in range(n)]
        for action in queries:
            mat = applyQuery((action[1], action[0]), (action[3], action[2]), mat)
        return mat 

    