"""Memory limit for an evaluation child process on Windows (NFR-10, SEC-04, TC-15).

On Linux and macOS the worker caps its own address space with ``resource.setrlimit``. Windows has no
such call, so the server puts the child in a *job object* whose per-process memory limit the operating
system enforces: an allocation beyond it fails, and Python raises ``MemoryError`` in the child, which
the worker reports as ``RESOURCE_LIMIT_EXCEEDED``. The job also kills the child if the server closes it.

The child is added to the job right after it starts, while the interpreter is still starting up and
long before the model is loaded, so the limit covers the model and the data.
"""

import ctypes
import logging
import subprocess
import sys

logger = logging.getLogger(__name__)

_JOB_OBJECT_EXTENDED_LIMIT_INFORMATION = 9
_JOB_OBJECT_LIMIT_PROCESS_MEMORY = 0x00000100
_JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE = 0x00002000


class _BasicLimits(ctypes.Structure):
    _fields_ = [
        ("PerProcessUserTimeLimit", ctypes.c_int64),
        ("PerJobUserTimeLimit", ctypes.c_int64),
        ("LimitFlags", ctypes.c_uint32),
        ("MinimumWorkingSetSize", ctypes.c_size_t),
        ("MaximumWorkingSetSize", ctypes.c_size_t),
        ("ActiveProcessLimit", ctypes.c_uint32),
        ("Affinity", ctypes.c_size_t),
        ("PriorityClass", ctypes.c_uint32),
        ("SchedulingClass", ctypes.c_uint32),
    ]


class _IoCounters(ctypes.Structure):
    _COUNTERS = ("Reads", "Writes", "Other", "ReadBytes", "WriteBytes", "OtherBytes")
    _fields_ = [(name, ctypes.c_uint64) for name in _COUNTERS]


class _ExtendedLimits(ctypes.Structure):
    _fields_ = [
        ("BasicLimitInformation", _BasicLimits),
        ("IoInfo", _IoCounters),
        ("ProcessMemoryLimit", ctypes.c_size_t),
        ("JobMemoryLimit", ctypes.c_size_t),
        ("PeakProcessMemoryUsed", ctypes.c_size_t),
        ("PeakJobMemoryUsed", ctypes.c_size_t),
    ]


class WindowsMemoryLimit:
    """Holds the job object for one child process; ``close()`` it once the child has ended."""

    def __init__(self, handle):
        self._handle = handle

    def close(self) -> None:
        if self._handle:
            ctypes.windll.kernel32.CloseHandle(self._handle)
            self._handle = None


def limit_child_memory(process: subprocess.Popen, limit_bytes: int) -> WindowsMemoryLimit | None:
    """On Windows, cap ``process`` at ``limit_bytes``. Elsewhere (and for a limit of 0) do nothing.

    If the operating system refuses, the evaluation still runs with its time limit, and a warning is
    logged, so a missing limit is visible to the operator.
    """
    if sys.platform != "win32" or limit_bytes <= 0:
        return None
    kernel32 = ctypes.windll.kernel32
    kernel32.CreateJobObjectW.restype = ctypes.c_void_p
    handle, pointer = ctypes.c_void_p, ctypes.c_void_p
    kernel32.SetInformationJobObject.argtypes = [handle, ctypes.c_int, pointer, ctypes.c_uint32]
    kernel32.AssignProcessToJobObject.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
    kernel32.CloseHandle.argtypes = [ctypes.c_void_p]

    job = kernel32.CreateJobObjectW(None, None)
    if not job:
        logger.warning("Could not create a job object; the memory limit is not applied")
        return None
    limits = _ExtendedLimits()
    flags = _JOB_OBJECT_LIMIT_PROCESS_MEMORY | _JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
    limits.BasicLimitInformation.LimitFlags = flags
    limits.ProcessMemoryLimit = limit_bytes
    applied = kernel32.SetInformationJobObject(
        job, _JOB_OBJECT_EXTENDED_LIMIT_INFORMATION, ctypes.byref(limits), ctypes.sizeof(limits)
    ) and kernel32.AssignProcessToJobObject(job, int(process._handle))
    if not applied:
        error = ctypes.GetLastError()
        logger.warning("Could not apply the memory limit to the evaluation process (error %s)", error)
        kernel32.CloseHandle(job)
        return None
    return WindowsMemoryLimit(job)
