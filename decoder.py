import struct
import argparse

def swap32(x):
    return struct.unpack("<I", struct.pack(">I", x))[0]


def decode_frequency(raw):
    try:
        step1 = raw // 100
        hex_str = str(step1)
        freq = int(hex_str, 16)
        return freq
    except:
        return None


def is_reasonable_freq(freq):
    return 1000000 < freq < 2000000000


def scan_for_frequencies(data, verbose=False):
    print("[*] Scanning for possible encoded frequencies (RAW MODE)...\n")

    for i in range(0, len(data) - 4):
        raw = struct.unpack_from("<I", data, i)[0]

        # Skip empty / boring values
        if raw == 0:
            continue

        # Focus near your known hit to reduce spam
        if i < 0x200 or i > 0x250:
            continue

        print(f"[Offset 0x{i:08X}]")
        print(f"    Raw          : {raw}")
        print(f"    Raw HEX      : {hex(raw)}")

        # Different scaling attempts
        print(f"    /100         : {raw / 100}")
        print(f"    /1000        : {raw / 1000}")
        print(f"    /10000       : {raw / 10000}")

        # Swap test
        swapped = swap32(raw)
        print(f"    Swapped      : {swapped}")
        print(f"    Swapped HEX  : {hex(swapped)}")

        # Swap scaling too
        print(f"    Swapped/100  : {swapped / 100}")
        print(f"    Swapped/1000 : {swapped / 1000}")

        print()


def parse_header(data):
    sig = struct.unpack_from("<I", data, 0)[0]
    version = struct.unpack_from("<I", data, 4)[0]

    print("[*] Header:")
    print(f"    Signature : 0x{sig:08X} ({sig.to_bytes(4, 'little')})")
    print(f"    Version   : {swap32(version)}")
    print()


def parse_aglo_table(data, offset=0x200):
    print(f"[*] Parsing AGLO table at 0x{offset:X}")

    try:
        row_count = swap32(struct.unpack_from("<I", data, offset)[0])
    except:
        print("[!] Failed to read row count")
        return

    print(f"    Row Count: {row_count}\n")

    ptr = offset + 4

    for i in range(row_count):
        base = ptr + (i * 54)

        try:
            raw_freq = struct.unpack_from("<I", data, base + 6)[0]
            freq = decode_frequency(swap32(raw_freq))

            enc_method = data[base + 17]

            print(f"[Row {i}] @ 0x{base:08X}")
            print(f"    Enc Method : {enc_method}")

            if freq:
                print(f"    Frequency : {freq} Hz ({freq/1e6:.3f} MHz)")
            else:
                print(f"    Frequency : (invalid)")

        except Exception as e:
            print(f"[!] Failed parsing row {i}: {e}")

        print()


def main():
    parser = argparse.ArgumentParser(description="CFT / alice.cft decoder tool")

    parser.add_argument("file", help="Input file")
    parser.add_argument("--scan", action="store_true", help="Scan for encoded frequencies")
    parser.add_argument("--parse", action="store_true", help="Parse structured table")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")

    args = parser.parse_args()

    with open(args.file, "rb") as f:
        data = f.read()

    print(f"[*] Loaded file: {args.file} ({len(data)} bytes)\n")

    parse_header(data)

    if args.scan:
        scan_for_frequencies(data, args.verbose)

    if args.parse:
        parse_aglo_table(data)


if __name__ == "__main__":
    main()