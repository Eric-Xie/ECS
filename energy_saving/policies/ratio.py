
DEFAULT_PERCENT = 0

class RatioPolicy(object):

    def __init__(self, percent=None):
        super(RatioPolicy, self).__init__()
        self.percent =\
            percent if percent else DEFAULT_PERCENT

    def check(self, **kwargs):
        on_with_vms = kwargs.get('on_with_vms')
        on_without_vms = kwargs.get('on_without_vms')
        off_without_vms = kwargs.get('off_without_vms')
        result = {}
        expect_on = on_with_vms * int(self.percent) / 100
        if on_without_vms > expect_on:
            result['power_off'] = on_without_vms - expect_on
        elif on_without_vms < expect_on:
            result['power_on'] = min(
                (expect_on-on_without_vms),
                off_without_vms
            )
        return result