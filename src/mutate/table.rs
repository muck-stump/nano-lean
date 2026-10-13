pub use crate::schema::Ref;
use crate::schema::{ExprKind, META};
use serde_json::Value;
use std::collections::BTreeSet;

pub fn defines(entry: &Value) -> Option<(Ref, u64)> {
    Ref::ALL
        .into_iter()
        .find_map(|r| Some((r, entry.get(r.key())?.as_u64()?)))
}

pub fn is_declaration(entry: &Value) -> bool {
    defines(entry).is_none() && entry.get(META).is_none()
}

pub fn id_at(line: &Value, ptr: &str) -> u64 {
    line.pointer(ptr)
        .and_then(Value::as_u64)
        .expect("refs point at ids")
}

pub fn refs(entry: &Value) -> Vec<(Ref, String)> {
    use Ref::{Expr, Level, Name};
    let mut out = Vec::new();
    let mut at = |kind: Ref, ptr: String| match entry.pointer(&ptr) {
        Some(Value::Array(items)) => {
            out.extend((0..items.len()).map(|i| (kind, format!("{ptr}/{i}"))));
        }
        Some(Value::Number(_)) => out.push((kind, ptr)),
        _ => {}
    };
    match defines(entry) {
        Some((Name, _)) => {
            at(Name, "/str/pre".into());
            at(Name, "/num/pre".into());
        }
        Some((Level, _)) => {
            for k in ["succ", "max", "imax"] {
                at(Level, format!("/{k}"));
            }
            at(Name, "/param".into());
        }
        Some((Expr, _)) => {
            at(Level, "/sort".into());
            at(Name, "/const/name".into());
            at(Level, "/const/us".into());
            at(Expr, "/app/fn".into());
            at(Expr, "/app/arg".into());
            for b in [
                ExprKind::Lam.key(),
                ExprKind::ForallE.key(),
                ExprKind::LetE.key(),
            ] {
                at(Name, format!("/{b}/name"));
                for k in ["type", "value", "body"] {
                    at(Expr, format!("/{b}/{k}"));
                }
            }
            at(Name, "/proj/typeName".into());
            at(Expr, "/proj/struct".into());
            at(Expr, "/mdata/expr".into());
        }
        None => {
            let Some((kind, body)) = entry.as_object().and_then(|o| o.iter().next()) else {
                return out;
            };
            let mut decl = |prefix: String, body: &Value| {
                for k in ["name", "levelParams", "all", "ctors", "induct"] {
                    at(Name, format!("{prefix}/{k}"));
                }
                at(Expr, format!("{prefix}/type"));
                at(Expr, format!("{prefix}/value"));
                for i in 0..body["rules"].as_array().map_or(0, Vec::len) {
                    at(Name, format!("{prefix}/rules/{i}/ctor"));
                    at(Expr, format!("{prefix}/rules/{i}/rhs"));
                }
            };
            if kind == "inductive" {
                for section in ["types", "ctors", "recs"] {
                    for (i, item) in body[section].as_array().into_iter().flatten().enumerate() {
                        decl(format!("/inductive/{section}/{i}"), item);
                    }
                }
            } else if kind != META {
                decl(format!("/{kind}"), body);
            }
        }
    }
    out
}

/// Drops definitions nothing reachable from a declaration or a pin uses, keeping ids as
/// they are so an edit re-applied at the returned pins means exactly what it meant before.
pub fn compact(lines: &[Value], pins: &[usize]) -> (Vec<Value>, Vec<usize>) {
    let mut live: BTreeSet<(Ref, u64)> = BTreeSet::new();
    for (i, line) in lines.iter().enumerate().rev() {
        let keep = match defines(line) {
            Some(d) => pins.contains(&i) || live.contains(&d),
            None => true,
        };
        if keep {
            for (kind, ptr) in refs(line) {
                live.insert((kind, id_at(line, &ptr)));
            }
        }
    }
    let mut seen = BTreeSet::new();
    let (mut out, mut at) = (Vec::new(), vec![usize::MAX; lines.len()]);
    for (i, line) in lines.iter().enumerate() {
        let pinned = pins.contains(&i);
        if let Some(d) = defines(line)
            && !pinned
            && (!live.contains(&d) || !seen.insert(d))
        {
            continue;
        }
        at[i] = out.len();
        out.push(line.clone());
    }
    (out, pins.iter().map(|&p| at[p]).collect())
}
