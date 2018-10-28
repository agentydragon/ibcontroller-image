#!/bin/bash
exec socat TCP-LISTEN:4452,fork TCP:127.0.0.1:4001
