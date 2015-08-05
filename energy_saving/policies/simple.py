
DEFAULT_RESERVATION = 1

class SimplePolicy(object):

    def __init__(self, reservation=None):
        super(SimplePolicy, self).__init__()
        self.reservation = \
            reservation if reservation else DEFAULT_RESERVATION

    def check(self, **kwargs):
        on_without_vms = int(kwargs.get('on_without_vms'))
        off_without_vms = int(kwargs.get('off_without_vms'))
        result = {}
        if on_without_vms > self.reservation:
            result['power_off'] = on_without_vms - self.reservation
        elif self.reservation > on_without_vms and\
            off_without_vms >= (self.reservation - on_without_vms):
            result['power_on'] = self.reservation - on_without_vms

        return result
