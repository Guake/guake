from guake.utils import attach_methods


def test__attach_methods():
    param1 = 1
    param2 = 2

    class Src(object):

        def get_param1(self):
            return self.param1

        def set_param2(self):
            self.param2 = param2

        def get_param3(self):
            return 3

    class Dst(object):

        def __init__(self):
            self.param1 = param1
            self.param3 = 4

        def get_param3(self):
            return self.param3

    dst = Dst()
    attach_methods(Src, dst)
    dst.set_param2()
    assert dst.get_param1() == dst.param1
    assert dst.param2 == param2
    assert dst.get_param3() == dst.param3
