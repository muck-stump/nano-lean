# Changelog

## Unreleased

- Split the Mathlib CI script into shell and Python files and drop the perf probe.
- Gate quotient reduction on `Quot` declarations.
- Reject quotient names on other declarations.
- Add `quot-axiom` mutation operator.
- Report rejections over unsupported in `nl-fast` exit code.
- Bound importer memory on sparse ids.
- Accept missing `"all"` groups like the reference loader.
- Cap `Nat.pow` result size.
- Derive reserved binder names from the lexer.
- Share JSON helpers, schema keys and projection checks.
- Check the owning block for `--declaration` on a generated name.
- Reject oversized universe offsets in the parser.
- Keep budget errors distinct in `Error::context`.
- Export `Expr` and `Level` under `kernel`.
- Add `Nat.log2` to the reference kernel.
- Unfold oversized `Nat.pow` and `Nat.shiftLeft` as Lean does.
- Pin Rust 1.97.1, elan 4.2.4 and olean-export 0.2.0.
- Check Mathlib and corpora as blean in CI.
- Upgrade olean-export to 0.3.0.
- Replace `stacker` with a stack floor guard that declines a declaration instead of overflowing.
- Return value checker rejections and declines through `R` instead of unwinding.
- Return reference checker rejections and declines through `R` and drop the panic channel.
- Pin function alignment to 64 bytes so code placement cannot move the hot loops.

## 0.1.0 (2026-10-08)

- Initial release.
