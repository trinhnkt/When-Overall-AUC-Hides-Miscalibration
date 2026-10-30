"""C3 follow-up: Reference [21] year 2027, as in Springer's 'Cite this paper' block (read by the supervisor on 2026-10-28)
and the Crossref print date; First Online was 2026-09-05."""
import sys

from msedit import apply, sub


def edit(body, path) -> None:
    sub(body, "X. Yan, C. Tang, and A. Shimada", "vol. 16946. Springer, 2026, pp.", "vol. 16946. Springer, 2027, pp.")


if __name__ == "__main__":
    apply(edit, "--write" in sys.argv)
