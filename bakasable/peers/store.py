from sortedcontainers import SortedDict

from bakasable import entities


class PeerStore(SortedDict):
    def add(self, *args):
        for peer in args:
            self[peer.uid] = peer

    def get_closest_uid(self, uid):
        index = self.bisect(uid)
        try:
            up = self.iloc[index]
        except IndexError:
            return self.iloc[index-1]

        try:
            down = self.iloc[index-1]
        except IndexError:
            return up

        return min([up, down], key=lambda x: abs(x - uid))

    def get_closest_peer(self, uid):
        return self[self.get_closest_uid(uid)]
