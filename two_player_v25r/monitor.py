"""Windows process-lifetime peak RSS with one persistent ctypes binding.

No per-call ctypes types, pointer registrations, caches or history are created.
The PROCESS_MEMORY_COUNTERS layout and PeakWorkingSetSize match the original
monitor; measurement failures remain errors.
"""
import ctypes
import os
from ctypes import wintypes


class Counters(ctypes.Structure):
    _fields_ = [('cb', wintypes.DWORD), ('PageFaultCount', wintypes.DWORD)] + [
        (name, ctypes.c_size_t) for name in (
            'PeakWorkingSetSize', 'WorkingSetSize',
            'QuotaPeakPagedPoolUsage', 'QuotaPagedPoolUsage',
            'QuotaPeakNonPagedPoolUsage', 'QuotaNonPagedPoolUsage',
            'PagefileUsage', 'PeakPagefileUsage')]


COUNTERS_POINTER = ctypes.POINTER(Counters)
_kernel = _psapi = _current_process = _memory_info = None
if os.name == 'nt':
    _kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    _psapi = ctypes.WinDLL('psapi', use_last_error=True)
    _current_process = _kernel.GetCurrentProcess
    _current_process.argtypes = []
    _current_process.restype = wintypes.HANDLE
    _memory_info = _psapi.GetProcessMemoryInfo
    _memory_info.argtypes = [wintypes.HANDLE, COUNTERS_POINTER, wintypes.DWORD]
    _memory_info.restype = wintypes.BOOL


def process_peak_rss():
    """Return lifetime PeakWorkingSetSize bytes; unsupported hosts return None."""
    if os.name != 'nt':
        return None
    memory = Counters()
    memory.cb = ctypes.sizeof(memory)
    if not _memory_info(_current_process(), ctypes.byref(memory), memory.cb):
        raise OSError(ctypes.get_last_error(), 'GetProcessMemoryInfo failed')
    return int(memory.PeakWorkingSetSize)
