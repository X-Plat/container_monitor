# container_monitor

This repository contains the source code for container monitor to 
update the container history and update link to a common interface
to other platforms.

## Summary

This container monitor has released two monitor tasks:
1. Monitor the instance change event, and update the container in
terface.
2. Monitor the container change event, and update the container h
istory, for application tracking.

## Getting started

The following instructions may help you get started with lsp
manager in a standalone environment.

### Setup

```
git clone https://github.com/X-Plat/container_monitor
cd container_monitor
python setup.py install

```

### Start

```
cd container_monitor/bin
./container_monitor
```

### Usage

## Notes

* 18/08/13: Instance event monitor released.
* 07/01/14: Container event monitor released.
