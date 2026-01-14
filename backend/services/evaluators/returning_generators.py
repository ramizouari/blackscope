from typing import Generator, Any, TypeVar, Generic, Union


YieldT = TypeVar('YieldT')
SendT = TypeVar('SendT')
ReturnT = TypeVar('ReturnT')


class ValueNotAvailableError(Exception):
    """Raised when trying to access return value before generator is exhausted"""

    def __init__(self):
        super().__init__("Return value not available yet")


class ReturningGenerator(Generic[YieldT, SendT, ReturnT]):
    def __init__(self, gen: Union[Generator[YieldT, SendT, ReturnT], "ReturningGenerator[YieldT, SendT, ReturnT]"]):
        if isinstance(gen, ReturningGenerator):
            self.gen = gen.gen
            self._return_value = gen._return_value
            self._exhausted = gen._exhausted
        else:
            self.gen = gen
            self._return_value: ReturnT | None = None
            self._exhausted = False

    @property
    def value(self) -> ReturnT:
        """Get the return value, raising exception if not available yet"""
        if not self._exhausted:
            raise ValueNotAvailableError()
        return self._return_value

    def exhaust(self) -> ReturnT:
        """Exhaust the generator and return the value"""
        if not self._exhausted:
            # Create iterator if not already created
            for _ in self:
                pass
        return self._return_value

    def __iter__(self) -> YieldT:
        """Manual iteration support"""
        self._return_value = yield from self.gen
        self._exhausted = True

    def __next__(self) -> YieldT:
        return self.send(None)

    def send(self, value: SendT) -> YieldT:
        """Send a value to the generator"""
        return self.gen.send(value)

    def throw(self, typ, val=None, tb=None):
        """Throw an exception into the generator"""
        return self.gen.throw(typ, val, tb)

    def close(self):
        """Close the generator"""
        return self.gen.close()

    def __enter__(self):
        """Context manager support"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager cleanup"""
        self.close()