"""Fold 5 explained in Data and Code Availability (review item 4). No number changed; changed run is red. Dry run unless --write."""
import sys
from msedit import apply, sub

def edit(body, path):
    sub(body, "Artifact v4 contains",
        "an additional run (fold 5) that this paper does not report,",
        "the prediction exports of one additional run (labelled fold 5 in the artifact, added after the "
        "analysis plan; its training logs are included) that this paper does not report,",
        allow_flatten=True)

if __name__ == "__main__":
    apply(edit, "--write" in sys.argv)

