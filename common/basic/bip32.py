from typing import List, Optional

BIP32_PRIME = 0x80000000
UINT32_MAX = (1 << 32) - 1


def decode_bip44_path(path: str) -> List[int]:
    def _parse_node(node: str) -> Optional[int]:
        if not node or node == "m" or node == "M":
            return None
        is_hardened = node.endswith("'") or node.endswith("h")
        node = node[:-1] if is_hardened else node
        try:
            child_index = int(node)
        except ValueError:
            child_index = None

        if child_index is None:
            return None

        if is_hardened:
            child_index = child_index | BIP32_PRIME

        if not (0 <= child_index <= UINT32_MAX):
            raise ValueError(f"bip32 path child index out of range: {child_index}")

        return child_index

    nodes = path.split("/")
    nodes = (_parse_node(i) for i in nodes)
    nodes = (i for i in nodes if i is not None)
    return list(nodes)


def encode_bip32_path(path_as_ints: List[int]) -> str:
    nodes = ["m"]
    for child_index in path_as_ints:
        if not isinstance(child_index, int):
            raise TypeError(f"bip32 path child index must be int: {child_index}")
        if not (0 <= child_index <= UINT32_MAX):
            raise ValueError(f"bip32 path child index out of range: {child_index}")

        prime = ""
        if child_index & BIP32_PRIME:
            prime = "'"
            child_index = child_index ^ BIP32_PRIME

        node = f"{child_index}{prime}"
        nodes.append(node)

    return "/".join(nodes)
