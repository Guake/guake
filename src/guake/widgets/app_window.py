
class ApplicationWindowMixin(object):

    def get_screen_size(self):
        return (200, 200)

    def prepare_to_draw(self):
        x, y = self.get_screen_size()
        self.set_default_size(x, y)
