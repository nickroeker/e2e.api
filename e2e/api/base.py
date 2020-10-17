"""Base classes for e2e.api internals."""

from typing import Any


class ClassInfo:
    """Methods for common class info."""

    @property
    def __fqualname__(self) -> str:
        """Gets the fully-qualified name for this class."""
        return self.fqualname_of(self)

    @property
    def __fname__(self) -> str:
        """Get the module-qualified path for the class.

        This will not properly communicate nested classes.
        """
        return self.fname_of(self)

    @staticmethod
    def fqualname_of(obj: Any) -> str:
        """Gets the fully-qualified name for the given object."""
        return "{}.{}".format(obj.__class__.__module__, obj.__class__.__qualname__)

    @staticmethod
    def fname_of(obj: Any) -> str:
        """Get the module-qualified path for the class.

        This will not properly communicate nested classes, functions, etc.
        """
        return "{}.{}".format(obj.__class__.__module__, obj.__class__.__name__)
