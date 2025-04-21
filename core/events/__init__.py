from ..logging import LoggingManager

logger = LoggingManager("Core.Events")

class EventManager:
    def __init__(self, bounce: bool = False):
        """
        A class representing an event system manager.

        Args:
            :bounce (bool): If True, will provide feedback if an event is emitted without any listeners
        """
        self.bounce = bounce
        self.events = {
            #"start": [func1, func2, func3],
        }
        self.globals = []

    def on(self, event: str):
        """
        Decorator for registering an event listener.

        Args:
            event (str): The event to listen for.

        Returns:
            None
        """
        def wrapper(func):
            if event not in self.events:
                self.events[event] = []

            self.events[event].append(func)
            logger.debug(f"Registered event listener {func.__name__ if hasattr(func, "__name__") else func} for {event}")


        return wrapper
    listen = on
    observe = on
    
    def listen_all(self, func):
        """
        Register a global event listener.
        WARNING: Do not create event listeners with the same names, as they will be voided.

        Args:
            func: The function to register as a global event listener.

        Returns:
            None
        """

        # for gf in self.globals:
        #     if gf.__name__ == func.__name__:
        #         return

        self.globals.append(func)

    def signal(self, event: str, *args, **kwargs):
        """
        Emit an event.

        Args:
            event (str): The event to emit.

        Returns:
            None
        """
        if event not in self.events:
            logger.debug(f"Event {event} bounced, no listeners registered (type 1)")
            return False
        
        if self.bounce and len(self.events[event]) == 0:
            logger.debug(f"Event {event} bounced, no listeners registered (type 2)")
            return False
        
        for func in self.events[event]:
            logger.debug(f"Calling event listener {func.__name__} for {event}")
            func(*args, **kwargs)

        for func in self.globals:
            logger.debug(f"Calling global event listener {func.__name__} for {event}")
            func(event, *args, **kwargs)

        return True
    emit = signal

    def dettach(self, event: str, func):
        """
        Remove an event listener.

        Args:
            event (str): The event to remove the listener from.
            func: The function to remove.

        Returns:
            None
        """
        if event not in self.events:
            return

        self.events[event].remove(func)
        logger.debug(f"Removed event listener {func.__name__} for {event}")

EventBus = EventManager()