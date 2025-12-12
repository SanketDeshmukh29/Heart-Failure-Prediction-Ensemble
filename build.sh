#!/usr/bin/env bash
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

Then in Render, set your build command to:
```
./build.sh