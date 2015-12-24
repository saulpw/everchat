
g_users = { } # [userauth] = <User object>

class User:
    def __init__(self, email):
        self.email = email
        self.channels = { } # ["ChannelName"] = "nick"

    def __str__(self):
        return self.email

    @staticmethod
    def find(ident, chan=None):
        """User.get(nickname, channel)
       or  User.get(email)"""

        if chan:
            if ident in chan.members:
                return chan.members[ident]
        else:
            if ident in g_users:
                return g_users[ident]

    @staticmethod
    def create(ident):
        u = User(ident)
        g_users[ident] = u

        return u

    def notify(self, obj):
        if self.connection:
            self.connection.notify(obj)

    def invite(self, destchan):
        pass
