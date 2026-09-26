"""Exercise the BTF loader, not just the shared library's presence."""

import ctypes
import ctypes.util


def main() -> None:
    name = ctypes.util.find_library("bpf")
    assert name is not None
    library = ctypes.CDLL(name)
    library.libbpf_get_error.argtypes = [ctypes.c_void_p]
    library.libbpf_get_error.restype = ctypes.c_long
    library.btf__load_vmlinux_btf.restype = ctypes.c_void_p
    library.btf__free.argtypes = [ctypes.c_void_p]
    btf = library.btf__load_vmlinux_btf()
    assert btf and library.libbpf_get_error(btf) == 0, "cannot parse kernel BTF"
    library.btf__free(btf)


if __name__ == "__main__":
    main()
