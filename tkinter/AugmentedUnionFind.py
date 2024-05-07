class AugmentedUnionFind:
    def __init__(self, size):
        self.root = list(range(size))
        self.rank = [1] * size
        self.size = [1] * size  # Each component initially has one element
        self.last_similarity = [-1] * size  # Initialize with -1 or any default value indicating no merge yet
        self.root_name = ['default'] * size  # Initialize names as 'default'

    def find(self, x):
        if self.root[x] != x:
            self.root[x] = self.find(self.root[x])  # Path compression
        return self.root[x]

    def union(self, x, y, similarity):
        rootX = self.find(x)
        rootY = self.find(y)

        if rootX != rootY:
            if self.rank[rootX] > self.rank[rootY]:
                self.root[rootY] = rootX
                self.last_similarity[rootX] = similarity  # Store the similarity of the last merge
                self.size[rootX] += self.size[rootY]  # Update the size of the new root
            elif self.rank[rootX] < self.rank[rootY]:
                self.root[rootX] = rootY
                self.last_similarity[rootY] = similarity  # Store the similarity of the last merge
                self.size[rootY] += self.size[rootX]  # Update the size of the new root
            else:
                self.root[rootY] = rootX
                self.rank[rootX] += 1
                self.last_similarity[rootX] = similarity  # Store the similarity of the last merge
                self.size[rootX] += self.size[rootY]  # Update the size of the new root

        if self.get_root_name( rootX ) == "default" and self.get_root_name( rootY ) != "default":
            self.set_root_name( rootX, self.get_root_name( rootY ) )

    def connected(self, x, y):
        return self.find(x) == self.find(y)

    def get_last_similarity(self, x):
        rootX = self.find(x)
        return self.last_similarity[rootX]

    def set_root_name(self, x, name):
        rootX = self.find(x)
        self.root_name[rootX] = name

    def get_root_name(self, x):
        rootX = self.find(x)
        return self.root_name[rootX]

    def get_size(self, x):
        rootX = self.find(x)
        return self.size[rootX]
