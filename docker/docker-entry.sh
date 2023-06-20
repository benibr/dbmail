#!/bin/bash

RUN_DAEMON="${DBMAIL_DAEMON:=/usr/local/sbin/dbmail-imapd}"
WITH_ARGS="${DBMAIL_ARGS:=-D -v}"

$RUN_DAEMON $WITH_ARGS
