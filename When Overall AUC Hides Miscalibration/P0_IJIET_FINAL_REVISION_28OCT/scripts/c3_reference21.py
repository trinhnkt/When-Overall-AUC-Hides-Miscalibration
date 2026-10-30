"""C3: Reference [21] with the Springer book title, series, and volume (DOI metadata checked by c3_springer_meta.py)."""
import sys

from msedit import apply, sub

OLD = "in Proc. Eur. Conf. Mach. Learn. Princ. Pract. Knowl. Discov. Databases (ECML PKDD), 2026, pp. 586–602."
NEW = ("in Machine Learning and Knowledge Discovery in Databases. Research Track (ECML PKDD), Lecture Notes in Computer "
       "Science, vol. 16946. Springer, 2026, pp. 586–602.")


def edit(body, path) -> None:
    sub(body, "X. Yan, C. Tang, and A. Shimada", OLD, NEW)


if __name__ == "__main__":
    apply(edit, "--write" in sys.argv)
