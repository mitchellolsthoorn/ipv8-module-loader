from __future__ import absolute_import


class EventBus(object):

    def __init__(self):
        super(EventBus, self).__init__()
        self.processors_map = {}  # Map of event_type -> [callbacks]

    def add_processor(self, listener, event_types):
        for event_type in event_types:
            if event_type not in self.processors_map:
                self.processors_map[event_type] = []
            self.processors_map[event_type].append(listener)

    def remove_processor(self, listener, event_types):
        for event_type in event_types:
            if event_type in self.processors_map and listener in self.processors_map[event_type]:
                self.processors_map[event_type].remove(listener)

    def process(self, event):
        if event.type not in self.processors_map:
            return

        for processor in self.processors_map[event.type]:
            processor.process_event(event)
