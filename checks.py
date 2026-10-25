"""Checking and saving logic (no web code). Used by app.py."""
import hashlib
import hmac
import os
import re
import sqlite3
from datetime import datetime

import pandas as pd

ALLOWED = {"csv", "xlsx", "xls"}

# Columns that identify a row (e.g. ["employee_id"]). Leave empty to treat a row
# as a duplicate only when every column is identical to an earlier row.
DUPLICATE_KEY = []

BASE = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE, "hr.db")
RESERVED = {"change_log", "users"}

# All templates live in this folder: one file per template (.csv, .xlsx or .xls).
# The template's name is the file name without the extension.
TEMPLATE_DIR = os.path.join(BASE, "templates")

# "template": the table is named after the template the user picked (employees.csv -> table "employees").
# "file": the table is named after the uploaded file instead.
TABLE_NAME_FROM = "template"

def connect():
    conn = sqlite3.connect(DB_PATH, isolation_level=None)  # we manage transactions
    conn.execute(
        "CREATE TABLE IF NOT EXISTS change_log (id INTEGER PRIMARY KEY, changed_at TEXT, "
        "user TEXT, table_name TEXT, action TEXT, filename TEXT, rows_before INTEGER, "
        "rows_after INTEGER, details TEXT)"
    )
    conn.execute(
        "CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY COLLATE NOCASE, "
        "password_hash TEXT NOT NULL, is_admin INTEGER NOT NULL DEFAULT 0, created_at TEXT)"
    )
    if conn.execute("SELECT 1 FROM users").fetchone() is None:
        # first start: one admin so you can sign in. Change this password straight away.
        conn.execute(
            "INSERT INTO users VALUES (?,?,?,?)", ("test", hash_password("test"), 1, now())
        )
    return conn


def _template_files():
    """{template name: file name} for every template file in the templates folder."""
    os.makedirs(TEMPLATE_DIR, exist_ok=True)
    found = {}
    for fn in sorted(os.listdir(TEMPLATE_DIR)):
        stem, dot, ext = fn.rpartition(".")
        if dot and stem and ext.lower() in ALLOWED and not fn.startswith("~$"):  # ~$ = Excel temp files
            found.setdefault(stem, fn)
    return found


def list_templates():
    return list(_template_files())


def load_template(name):
    """The template the user picked. Returns [(sheet name, [(column, type), ...]), ...].
    Header row = column names and order, example row(s) = data types.
    A CSV template (or a workbook with one sheet) has just one entry."""
    files = _template_files()
    if name not in files:  # only names that exist in the folder are accepted, never a typed path
        raise FileNotFoundError("that template does not exist")
    fn = files[name]
    sheets = read_file(os.path.join(TEMPLATE_DIR, fn), fn.rsplit(".", 1)[-1].lower())
    if not sheets:
        raise ValueError("the template has no sheets")
    result = []
    for sheet, df in sheets.items():
        where = f" (sheet '{sheet}')" if len(sheets) > 1 else ""
        cols = list(df.columns)
        if df.empty or any(c.startswith("Unnamed:") for c in cols):
            raise ValueError("it needs a header row with a name for every column and at least one example row" + where)
        types = [column_type(df[c]) for c in cols]
        if None in types:
            raise ValueError("every column needs an example value in the template" + where)
        result.append((sheet, list(zip(cols, types))))
    if len(result) > 1:
        names = [clean_table_name(sheet) for sheet, _ in result]
        if len(set(names)) < len(names):
            raise ValueError("two sheets have names that would give the same table name")
    return result


def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def table_name_for(filename):
    return clean_table_name(os.path.splitext(filename)[0])


def clean_table_name(stem):
    name = re.sub(r"[^0-9a-zA-Z]+", "_", stem).strip("_").lower()
    if not name or name[0].isdigit():
        name = "t_" + name
    return name


def _tidy(df):
    df.columns = [str(c).strip() for c in df.columns]
    return df.replace(r"^\s*$", pd.NA, regex=True)


def read_file(path, ext):
    """Returns {sheet name: table}. A CSV file has just one table, under the name None."""
    if ext == "csv":
        try:
            df = pd.read_csv(path, encoding="utf-8-sig")
        except UnicodeDecodeError:
            if hasattr(path, "seek"):
                path.seek(0)  # go back to the start of the file before trying again
            df = pd.read_csv(path, encoding="latin-1")
        return {None: _tidy(df)}
    sheets = pd.read_excel(path, sheet_name=None)  # every sheet; .xls needs the xlrd package
    return {str(name).strip(): _tidy(df) for name, df in sheets.items()}


def column_type(series):
    had_null = series.isna().any()
    s = series.dropna()
    if s.empty:
        return None  # nothing to judge: every value is empty
    if had_null and pd.api.types.is_float_dtype(s) and len(s) and (s % 1 == 0).all():
        s = s.astype("int64")  # whole numbers only look like floats because of blanks
    if pd.api.types.is_bool_dtype(s):
        return "BOOLEAN"
    if pd.api.types.is_integer_dtype(s):
        return "INTEGER"
    if pd.api.types.is_float_dtype(s):
        return "REAL"
    if pd.api.types.is_datetime64_any_dtype(s):
        return "DATETIME"
    return "TEXT"


def rows_text(idx):
    shown = ", ".join(str(i + 2) for i in idx[:10])  # +2: header is row 1
    return shown + (", ..." if len(idx) > 10 else "")


def validate(df, template):
    """Return a list of problems. Empty list = file is good."""
    errors = []
    cols = list(df.columns)
    types = [column_type(df[c]) for c in cols]

    bad_headers = [c for c in cols if c.startswith("Unnamed:")]
    if bad_headers:
        errors.append("Some columns have no header name.")

    if template:  # same names, same order, same types; no extra columns allowed
        missing = [n for n, _ in template if n not in cols]
        if missing:
            errors.append("Missing column(s): " + ", ".join(missing))
        for i, (tname, ttype) in enumerate(template):
            if i >= len(cols):
                break
            if cols[i] != tname:
                if tname in cols:
                    errors.append(f"Column {i + 1} should be '{tname}' but is '{cols[i]}' (wrong order).")
                elif tname not in missing:
                    errors.append(f"Column {i + 1} should be '{tname}' but is '{cols[i]}'.")
            elif types[i] is not None and types[i] != ttype:
                errors.append(f"Column '{tname}' should contain {ttype} values but contains {types[i]}.")

    if template and len(cols) > len(template):
        extra = cols[len(template):]
        errors.append("Extra column(s) are not allowed: " + ", ".join(extra) + ". Remove them and upload again.")

    for c in cols:
        nulls = [i for i, v in enumerate(df[c].isna()) if v]
        if nulls:
            errors.append(f"Column '{c}' has {len(nulls)} empty value(s) (rows {rows_text(nulls)}).")

    key = DUPLICATE_KEY if DUPLICATE_KEY and all(k in cols for k in DUPLICATE_KEY) else None
    dups = [i for i, v in enumerate(df.duplicated(subset=key)) if v]
    if dups:
        what = "with the same " + ", ".join(key) if key else "identical to an earlier row"
        errors.append(f"{len(dups)} duplicate row(s) {what} (rows {rows_text(dups)}).")
    return errors


def clean(v):
    if isinstance(v, pd.Timestamp):
        return v.isoformat(sep=" ")
    return v.item() if hasattr(v, "item") else v


def q(name):
    return '"' + name.replace('"', '""') + '"'


def log(conn, user, table, action, filename, before, after, details):
    conn.execute(
        "INSERT INTO change_log (changed_at, user, table_name, action, filename, rows_before, "
        "rows_after, details) VALUES (?,?,?,?,?,?,?,?)",
        (now(), user, table, action, filename, before, after, details),
    )


def handle_file(conn, f, filename, user, template_name):
    """f is any file-like object (the uploaded file); filename is its name;
    template_name is the template the user picked from the list.
    A template with several sheets creates one table per sheet (<name>_<sheet>).
    Either every sheet is accepted and saved, or nothing is changed."""
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if TABLE_NAME_FROM == "template" and template_name:
        base = clean_table_name(template_name)
    else:
        base = table_name_for(filename)
    result = {"file": filename, "table": base, "template": template_name,
              "status": "rejected", "errors": [], "tables": []}

    def reject(errors):
        """Every rejection is written to the change log, whatever the reason."""
        result["errors"] = errors
        log(conn, user, base, "REJECTED", filename, None, None, f"template {template_name}: " + " | ".join(errors))
        return result

    if template_name not in list_templates():
        return reject(["Choose a template from the list."])
    if ext not in ALLOWED:
        return reject(["Only CSV, XLSX and XLS files are allowed."])
    try:
        sheets = read_file(f, ext)
    except Exception as e:
        return reject([f"The file could not be read ({type(e).__name__}). Check it is not damaged."])
    if not sheets:
        return reject(["The file has no sheets."])
    try:
        template = load_template(template_name)
    except Exception as e:
        return reject([f"The template file has a problem: {e}. Ask the administrator to fix it."])

    multi = len(template) > 1
    errors, jobs = [], []  # jobs: (table name, data, sheet name)
    if not multi:
        df = next(iter(sheets.values()))  # the only table of a CSV, or the first sheet of a workbook
        errors += ["The file has no data rows."] if df.empty else validate(df, template[0][1])
        jobs.append((base, df, template[0][0]))
    else:
        if ext == "csv":
            return reject(["This template has several sheets, so upload an Excel file (XLSX or XLS)."])
        have = {s.lower(): s for s in sheets}  # sheet names are not case sensitive; their order does not matter
        wanted = {s.lower() for s, _ in template}
        missing = [s for s, _ in template if s.lower() not in have]
        extra = [s for s in sheets if s.lower() not in wanted]
        if missing:
            errors.append("Missing sheet(s): " + ", ".join(missing))
        if extra:
            errors.append("Extra sheet(s) are not allowed: " + ", ".join(extra))
        for sheet, tcols in template:
            if sheet.lower() not in have:
                continue
            df = sheets[have[sheet.lower()]]
            found = ["The sheet has no data rows."] if df.empty else validate(df, tcols)
            errors += [f"Sheet '{sheet}': {e}" for e in found]
            jobs.append((clean_table_name(f"{base}_{sheet}"), df, sheet))
    for table, _, _ in jobs:
        if table in RESERVED or table.startswith("sqlite_"):
            errors.append(f"The name '{table}' is reserved. Rename the template (or the file).")
    if errors:
        return reject(errors)

    try:
        conn.execute("BEGIN")
        for table, df, sheet in jobs:
            exists = conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)).fetchone()
            cols = list(df.columns)
            types = [column_type(df[c]) for c in cols]
            rows = [tuple(clean(v) for v in r) for r in df.itertuples(index=False, name=None)]
            before = conn.execute(f"SELECT COUNT(*) FROM {q(table)}").fetchone()[0] if exists else None
            if exists:
                conn.execute(f"DROP TABLE {q(table)}")
            conn.execute(f"CREATE TABLE {q(table)} (" + ", ".join(f"{q(c)} {t}" for c, t in zip(cols, types)) + ")")
            conn.executemany(f"INSERT INTO {q(table)} VALUES ({','.join('?' * len(cols))})", rows)
            action = "REPLACED" if exists else "CREATED"
            details = f"{len(cols)} columns, template {template_name}" + (f", sheet {sheet}" if multi else "")
            log(conn, user, table, action, filename, before, len(rows), details)
            result["tables"].append({"table": table, "status": action.lower(), "rows": len(rows)})
        conn.execute("COMMIT")
    except Exception as e:
        conn.execute("ROLLBACK")
        result["tables"] = []
        result["errors"].append(f"Saving failed, nothing was changed ({type(e).__name__}).")
        return result

    result["status"] = "replaced" if any(t["status"] == "replaced" for t in result["tables"]) else "created"
    result["rows"] = sum(t["rows"] for t in result["tables"])
    result["table"] = ", ".join(t["table"] for t in result["tables"])
    return result


# ---------------- users and roles ----------------
ITERATIONS = 200_000


def hash_password(password):
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, ITERATIONS)
    return f"pbkdf2${ITERATIONS}${salt.hex()}${digest.hex()}"


def check_password(password, stored):
    try:
        _, iters, salt, digest = stored.split("$")
        test = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), int(iters))
        return hmac.compare_digest(test.hex(), digest)
    except Exception:
        return False


def verify_login(username, password):
    conn = connect()
    try:
        row = conn.execute("SELECT password_hash FROM users WHERE username=?", (username or "",)).fetchone()
    finally:
        conn.close()
    return bool(row) and check_password(password or "", row[0])


def is_admin(username):
    if not username:
        return False
    conn = connect()
    try:
        row = conn.execute("SELECT is_admin FROM users WHERE username=?", (username,)).fetchone()
    finally:
        conn.close()
    return bool(row and row[0])


def list_users():
    conn = connect()
    try:
        return conn.execute("SELECT username, is_admin, created_at FROM users ORDER BY username").fetchall()
    finally:
        conn.close()


def _admin_count(conn):
    return conn.execute("SELECT COUNT(*) FROM users WHERE is_admin=1").fetchone()[0]


def save_user(actor, username, password, make_admin):
    """Add a user, or update an existing one (blank password = keep the old one). Admins only."""
    if not is_admin(actor):
        return "Only admins can change users."
    username = (username or "").strip()
    if not re.fullmatch(r"[A-Za-z0-9_.@-]{1,50}", username):
        return "Username must be 1-50 characters: letters, numbers, . _ @ -"
    if password and len(password) < 8:
        return "The password must be at least 8 characters."
    make_admin = 1 if make_admin else 0

    conn = connect()
    try:
        row = conn.execute("SELECT is_admin FROM users WHERE username=?", (username,)).fetchone()
        if row is None and not password:
            return "A new user needs a password."
        if row and row[0] and not make_admin and _admin_count(conn) <= 1:
            return "There must be at least one admin."
        conn.execute("BEGIN")
        if row is None:
            conn.execute("INSERT INTO users VALUES (?,?,?,?)", (username, hash_password(password), make_admin, now()))
            action, details, msg = "USER_ADDED", f"{username} admin={bool(make_admin)}", f"User '{username}' added."
        else:
            if password:
                conn.execute("UPDATE users SET is_admin=?, password_hash=? WHERE username=?",
                             (make_admin, hash_password(password), username))
            else:
                conn.execute("UPDATE users SET is_admin=? WHERE username=?", (make_admin, username))
            action = "USER_UPDATED"
            details = f"{username} admin={bool(make_admin)}, password {'changed' if password else 'unchanged'}"
            msg = f"User '{username}' updated."
        log(conn, actor, "users", action, None, None, None, details)
        conn.execute("COMMIT")
        return msg
    except Exception as e:
        conn.execute("ROLLBACK")
        return f"Could not save the user ({type(e).__name__}). Nothing was changed."
    finally:
        conn.close()


def delete_user(actor, username):
    if not is_admin(actor):
        return "Only admins can change users."
    username = (username or "").strip()
    if username.lower() == (actor or "").lower():
        return "You cannot delete your own account."
    conn = connect()
    try:
        row = conn.execute("SELECT is_admin FROM users WHERE username=?", (username,)).fetchone()
        if row is None:
            return f"There is no user '{username}'."
        if row[0] and _admin_count(conn) <= 1:
            return "There must be at least one admin."
        conn.execute("BEGIN")
        conn.execute("DELETE FROM users WHERE username=?", (username,))
        log(conn, actor, "users", "USER_DELETED", None, None, None, username)
        conn.execute("COMMIT")
        return f"User '{username}' deleted."
    except Exception as e:
        conn.execute("ROLLBACK")
        return f"Could not delete the user ({type(e).__name__}). Nothing was changed."
    finally:
        conn.close()


def my_tables(username):
    """Tables this user has created or replaced, i.e. the ones they take part in."""
    conn = connect()
    try:
        return [
            r[0]
            for r in conn.execute(
                "SELECT DISTINCT table_name FROM change_log WHERE user = ? COLLATE NOCASE "
                "AND action IN ('CREATED', 'REPLACED') ORDER BY table_name",
                (username or "",),
            )
        ]
    finally:
        conn.close()