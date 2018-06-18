from sortedcontainers import SortedSet


class BaseThink:
    bag = set()

    def __init__(self, **param):
        self.action_param = param

    def __call__(self, func):
        self.callback = func
        self.bag.add(self)
        return func

    def test(self, param):
        return all(key in param and
                   (param[key] == value or isinstance(param[key], value))
                   for key, value in self.action_param.items())

    @classmethod
    def execute(cls, param):
        for event in cls.bag:
            if event.test(param):
                event.callback(**param)


class on_action(BaseThink):
    pass


class on_event(BaseThink):
    pass


class on_loop(BaseThink):
    bag = SortedSet(key=lambda e: e.priority)

    def __init__(self, **param):
        self.priority = param.pop('priority', 500)
        super().__init__(**param)

    @classmethod
    def exec_all(cls, context):
        cls.execute({'type': 'global', 'context': context})
        # TODO: execute for each type in store
