# Release Provenance

This repository is the reference-artifact and handoff package for the
single-inductor target-L optimizer. It is a separately initialized Git
repository rather than a branch of the development repository.

The maintainable source of truth is:

```text
C:\Users\mechrevo\Desktop\single_inductor_lq_surrogate
```

The release preserves a selected set of FDL, Cadence, GDS, Touchstone, and
best-result artifacts so a reviewer can inspect the evidence chain without
rerunning the complete EMX campaign. Source changes that should remain
maintained belong in the core repository first; this package should be updated
from a documented core snapshot.

The historical integration workspace at `新建文件夹 (2)` contains the broader
LVBOBALUN, filter, balun, cascade, and HFSS context. It is not a dependency of
the release package at runtime.
