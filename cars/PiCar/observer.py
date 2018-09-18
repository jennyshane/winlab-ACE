class Observer(object):
    observables={}
    def __init__(self):
        pass
    
    def observe(self, event_name, callback):
        if event_name in Observer.observables.keys():
            Observer.observables[event_name].append(callback)
        else:
            Observer.observables[event_name]=[callback]

class Flag(object):
    def __init__(self, name, attr_dict, autofire=True):
        self.name=name
        for key, value in attr_dict.items():
            setattr(self, key, value)
        if autofire:
            #print(self.name+"firing")
            self.fire()

    def fire(self, value=None):
        #print(self.name+"delayed fire")
        if value is not None:
            setattr(self, "value", value)
        if self.name in Observer.observables.keys():
            for cb in Observer.observables[self.name]:
                cb(self)
