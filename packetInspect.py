#!/usr/bin/env python3

# Packet inspector for csv files recorded in bitscope dso

import argparse, os, sys


def parseData(invertLogic, invertBits, verbose, nStopBits, timestamp, samplesPerBit, data):
    bitCount = 0
    sampleCount = 0
    startBit = 0
    stopBit = 0
    curByte = 0
    listBits = []
    listBytes = []
    high = 5
    low = 0

    # Invert Logic
    if invertLogic:
        high = 0
        low = 5

    for sample in data:
        # wait until we see a startBit
        if int(sample) == high and startBit == 0:
            sampleCount = 0
            continue

        if int(sample) == low and startBit == 0:
            sampleCount += 1
            if verbose:
                print("{0} Found Start Bit sampleCount={1}".format(sample, sampleCount))
            if sampleCount == round(samplesPerBit / 2):
                sampleCount = 0
                startBit = 1
                continue

        # we have a possible byte            
        if startBit == 1:
            sampleCount += 1
            if verbose:
                print("sample={0} count={1}".format(sample, sampleCount))

            # check for bit every n samples
            if sampleCount == samplesPerBit:
                sampleCount = 0
                bitCount += 1
                if bitCount < 9:
                    if int(sample) == high:
                        listBits.append("1")
                        if verbose:
                            print("{1} Bit {0} is 1 {2}".format(bitCount, sample, high))

                    if int(sample) == low:
                        listBits.append("0")
                        if verbose:
                            print("{1} Bit {0} is 0 {2}".format(bitCount, sample, low))

                # we should see a stop bit
                if bitCount > 8:
                    curByte += 1
                    stopBit += 1
                    if stopBit < nStopBits:
                        continue

                    if int(sample) == high and stopBit >= nStopBits:
                        if verbose:
                            print("Error: no stop bit! current byte:{2} current sample:{0} listBits:{1} Trying again".format(int(sample), listBits, curByte))

                        # don't reset counts, just try next bit
                        continue

                    if verbose:
                        print("We have a byte:")

                    bitCount = 0
                    startBit = 0
                    binaryString = "".join(listBits)

                    if invertBits:
                        binaryString = binaryString[::-1]

                    listBytes.append("{0:0>2X}".format(int(binaryString, 2)))
                    if verbose:
                        print(listBytes, listBits)

                    listBits.clear()

    print(timestamp, listBytes)
    curByte = 0


def main():
    invertLogic = 0
    invertBits = 0
    verbose = 0
    parser = argparse.ArgumentParser(description='Display information on a swiper.',
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('filepath', help='Path of bitscope csv output file')
    parser.add_argument('-b', metavar='<n>', nargs=1, default=[115200], type=int, help='Baud')
    parser.add_argument('-i', help='Invert byte (LSB on the left)', action='store_true')
    parser.add_argument('-l', help='Invert logic so 0v is a high (or 1)', action='store_true')
    # todo: parser.add_argument('-p', metavar='<n>', nargs=1, default=0, type=int, help='Number of parity bits')
    parser.add_argument('-s', metavar='<n>', nargs=1, default=[1], type=int, help='Number of stop bits')
    parser.add_argument('-c', metavar='<n>', nargs=1, default=[4], type=int, help='Channel to parse (note: D0-D7 starts at channel 4')
    parser.add_argument('-v', help='Debug', action='store_true')
    # todo: add different formats for output? Binary? ASCII?
    args = parser.parse_args()

    if args.l:
        invertLogic = 1

    if args.i:
        invertBits = 1

    if args.v:
        verbose = 1

    nStopBits = args.s[0]

    if not os.path.isfile(args.filepath):
        print("Error: {0} not found".format(args.filepath))
        sys.exit()

    with open(args.filepath, 'r') as f:
        for line in f:
            if "trigger" in line:
                continue

            ll = line.split(',')
            trigger = ll[0]  # Trigger count (for this session I think)
            stamp = ll[1]    # Timestamp
            channel = ll[2]  # Channel D0-D7 start at channel 4 for some reason
            index = ll[3]
            chtype = ll[4]
            delay = ll[5]
            factor = ll[6]
            rate = ll[7]     # Sample rate in Hz  (this number divided by baud should give us the expected number of samples per bit)
            count = ll[8]    # number of samples in data
            data = ll[9:]
            samplesPerBit = round(float(rate) / args.b[0])

            if int(channel) == args.c[0]:
                parseData(invertLogic, invertBits, verbose, nStopBits, stamp, samplesPerBit, data)


if __name__ == "__main__":
    main()
