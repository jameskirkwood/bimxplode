# BIMxplode

This project is an effort to reverse engineer the BIMx hyper-model format for architecture visualisation.

Examples of BIMx models are available for download without registration on [BIMx Model Transfer](https://bimx.graphisoft.com/).

# Installation

Python 3 is required.

Download the repository, change to the repository root directory, then:

```sh
python3 setup.py install --user
```

Or, for development:

```sh
pip3 install -e .
```

# Usage

```sh
bxpk -x model.bimx # extract a BXPK archive
bxpk -c ./* -f new.bimx # create a BXPK archive
bxpk -x new.bimx -l # list members of a BXPK archive
zres -x model2.bimx # extract a ZRES archive
bxpk -h # for complete `bxpk` usage documentation
zres -h # for complete `zres` usage documentation
```

# Encodings

Note: All integers are in little-endian byte order unless otherwise indicated.

## 🏠 BIMx

Some BIMx models begin with a four-byte magic string `BIMx`, however these were observed to be BXPK archives beginning with the contents of a four-byte member named `signature.txt`. On the other hand, some models were observed to be ZRES archives.

## 📦 BXPK

This is a flat uncompressed archive format.

BXPK format models were observed to contain various PNG images, XML documents, other BXPK and ZRES archives, and a file with the extension `.sda` whose format is yet to be investigated.

A 16-byte header (or trailer) is written at the end of the file. The layout of the header is as follows.

| Offset | Type | Interpretation
| - | - | -
| 0 | u32 | Number of files in the archive
| 4 | u32 | Size of the index
| 8 | u32 | Unknown (usually 1)
| 12 | u8[4] | Magic string `KPXB`
| 16 | - | (End of file)

I have taken the liberty of assuming that the magic string at the end of the file is in fact "BXPK" written backwards, as this could reasonably have stood for **B**IM**x** **P**ac**k**age. Furthermore, some BIMx models contain embedded BXPK archives with the extension `.bxp`.

### The Index

The index immediately precedes the header and contains one flexibly sized item for each file in the archive. The layout of each item is as follows.

| Offset | Type | Interpretation
| - | - | -
| 0 | u32 | Size of file name field (n)
| 4 | u8[n] | File name
| a = 4 + n | u64 | Unknown (usually zero)
| a + 8 | u64 | File size
| a + 16 | u64 | Offset of file contents in the archive
| a + 24 | u8[40] | ASCII coded hexadecimal digest
| a + 64 | - | (Next item in the index, or header if this is the last item)

### The Member "Digest" Field

This field always contains 40 hexadecimal digits. I refer to it as the "digest" because ARCHICAD 22.7 appears to set it to the SHA1 hash of the file contents for most embedded files. ARCHICAD 20.4012 sometimes stores something that looks like a hash, other times just the numbers 1 to 20 in BCD (assuming hexadecimal encoding). Further investigation is needed to determine the significance of this field.

## 📦 ZRES

This is a flat archive format. Files in a ZRES archive are usually compressed (see [QLZ](#🗜-qlz)).

ZRES format models were observed to contain TGA images, XML metadata and various binary files with recognisable names and contents. The binary files were also present in an embedded ZRES archive within a BXPK format model.

The 8-byte header (or trailer) at the end of the file has the following layout.

| Offset | Type | Interpretation
| - | - | -
| 0 | u32 | Number of records in the index
| 4 | u8[4] | Magic string `ZRES`
| 8 | - | (End of file)

### The Index

The index immediately precedes the header and contains a number of 520-byte records, which may describe an embedded file or be empty (all zero bytes). Non-empty index records have the following layout.

| Offset | Type | Interpretation
| - | - | -
| 0 | u8[512] | File name padded with zero bytes
| 512 | u32 | Offset of file contents in the archive
| 516 | u32 | File size
| 520 | - | (Next record in the index, or header if this is the last record)

## 🗜 QLZ

Within a ZRES archive, files beginning with the magic string `QLZ` are compressed using [QuickLZ](http://www.quicklz.com/) level 3. The bytes following the magic string may be decompressed without any additional information.

## 📇 OFS

TODO (see [ofs.py](src/bimxplode/codec/ofs.py))

## 📄 SDA

TODO (see [sda.py](docs/sda.py))

# Legal

[QuickLZ](http://www.quicklz.com/) is used to decompress some BIMx data. Its source code is only freely available under the terms of the GNU GPL versions 1, 2 and 3, therefore as I understand, this project must inherit one of those licences.
