import os

# To run locally not make it go through proxy 
os.environ["NO_PROXY"] = "127.0.0.1,localhost"
os.environ["no_proxy"] = "127.0.0.1,localhost"

import gradio as gr
import pandas as pd

import checks

STANDARD_NOTE = "You only see the tables you have uploaded to, and the changes made to them."  # shown to standard users
# =============== COPY THIS PART ===============
# ---------------------------------------------------------------------------
# ZAIN BRAND THEMING & STYLING
# ---------------------------------------------------------------------------
zain_teal = gr.themes.Color(
    c50="#e6f7f7",
    c100="#b3e8e8",
    c200="#80d8d9",
    c300="#4dc9ca",
    c400="#1ab9bb",
    c500="#00A3A6",  # Main Zain Teal/Turquoise
    c600="#008b8e",
    c700="#007275",
    c800="#005a5c",
    c900="#004143",
    c950="#00292a",
)

zain_purple = gr.themes.Color(
    c50="#f4eff9",
    c100="#dfd0ef",
    c200="#c9b0e4",
    c300="#b491da",
    c400="#9f71cf",
    c500="#5C2D91",  # Main Zain Purple
    c600="#512780",
    c700="#43206a",
    c800="#351954",
    c900="#27123d",
    c950="#1a0c29",
)

# Custom Theme definition
zain_theme = gr.themes.Soft(
    primary_hue=zain_teal,
    secondary_hue=zain_purple,
    neutral_hue="slate",
    font=[gr.themes.GoogleFont("Poppins"), "sans-serif"],
).set(
    button_primary_background_fill="*primary_500",
    button_primary_background_fill_hover="*primary_600",
    button_primary_text_color="#FFFFFF",
    block_title_text_color="*secondary_500",
)

# Custom CSS for Zain branding header and hiding default footer
custom_css = """
/* Zain Header Styling */
.zain-header {
    background: linear-gradient(135deg, #5C2D91 0%, #00A3A6 100%);
    padding: 24px 32px;
    border-radius: 12px;
    color: white;
    margin-bottom: 16px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.zain-header h1 {
    color: white !important;
    font-weight: 700;
    margin: 0;
    font-size: 2rem;
}

.zain-header p {
    color: rgba(255, 255, 255, 0.9) !important;
    margin: 6px 0 0 0;
    font-size: 1rem;
}

/* User Info Bar Styling */
.user-info-row {
    margin-bottom: 15px;
    align-items: center;
}

/* Tab Active Header Styling */
.tabs div button.selected {
    border-bottom-color: #00A3A6 !important;
    color: #5C2D91 !important;
    font-weight: 600;
}

/* Hide Gradio Footer Completely */
footer {
    display: none !important;
}
"""
# ---------------------------------------------------------------------------


def _user(request):  # the name of whoever is signed in, or None
    return getattr(request, "username", None)


def _admin(request):  # True only if that person is an admin in the users table
    return checks.is_admin(_user(request))


def whoami(request: gr.Request):  # the "Signed in as ..." line at the top of the page
    u = _user(request)
    if not u:
        return "Not signed in."
    return f"Signed in as **{u}** ({'admin' if checks.is_admin(u) else 'standard user'})."


def notices(request: gr.Request):  # a short note for standard users on the Tables and Change log tabs
    text = "" if _admin(request) else STANDARD_NOTE
    return text, text


def role_tabs(request: gr.Request):  # the Users tab is only shown to admins
    return gr.Tab(visible=_admin(request))

#=============== REPLACE THIS PART ===============
def upload_files(paths, request: gr.Request):
    if not paths:
        return "Choose at least one file first.", None
    user = _user(request) or "unknown"
    conn = checks.connect()
    parts = []
    try:
        for p in paths:
            path = p if isinstance(p, str) else p.name
            name = os.path.basename(path)
            with open(path, "rb") as f:
                r = checks.handle_file(conn, f, name, user)
            if r["status"] == "rejected":
                problems = "\n".join(f"- {e}" for e in r["errors"])
                parts.append(f"**{name}: REJECTED.** Nothing was changed.\n{problems}")
            else:
                what = "new table created" if r["status"] == "created" else "table replaced"
                parts.append(f"**{name}: accepted**, {what}: {r['table']} ({r['rows']} rows).")
    finally:
        conn.close()
    return "\n\n".join(parts), None  # None empties the file box


def list_tables(request: gr.Request):
    conn = checks.connect()
    names = [
        row[0]
        for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' "
            "AND name NOT IN ('change_log', 'users') AND name NOT LIKE 'sqlite_%' ORDER BY name"
        )
    ]
    conn.close()
    if not _admin(request):  # standard user only sees the tables they have taken part in
        mine = checks.my_tables(_user(request))
        names = [n for n in names if n in mine]
    return gr.Dropdown(choices=names, value=names[0] if names else None)


def show_table(name, request: gr.Request):
    if not name:
        return pd.DataFrame()
    if not _admin(request) and name not in checks.my_tables(_user(request)):
        return pd.DataFrame()
    conn = checks.connect()
    df = pd.read_sql_query(f"SELECT * FROM {checks.q(name)}", conn)
    conn.close()
    return df


def show_log(request: gr.Request):
    conn = checks.connect()
    if _admin(request):
        df = pd.read_sql_query("SELECT * FROM change_log ORDER BY id DESC", conn)
    else:  # standard users: their own entries + every change to tables they take part in
        user = _user(request) or ""
        mine = checks.my_tables(user)
        marks = ",".join("?" * len(mine))
        sql = "SELECT * FROM change_log WHERE action NOT LIKE 'USER_%' AND (user = ? COLLATE NOCASE"
        sql += f" OR table_name IN ({marks})" if mine else ""
        sql += ") ORDER BY id DESC"
        df = pd.read_sql_query(sql, conn, params=[user] + mine)
    conn.close()
    return df


def show_users(request: gr.Request):  # the users list, without the password hashes
    if not _admin(request):
        return pd.DataFrame()
    rows = [(u, "yes" if a else "no", c) for u, a, c in checks.list_users()]
    return pd.DataFrame(rows, columns=["NT", "admin", "created_at"])


def save_user_ui(username, password, make_admin, request: gr.Request):  # add or update a user
    msg = checks.save_user(_user(request), username, password, make_admin)
    return msg, show_users(request), ""  # clears password box


def delete_user_ui(username, request: gr.Request):  # delete a user
    msg = checks.delete_user(_user(request), username)
    return msg, show_users(request)


# Building the App UI
with gr.Blocks(title="Zain HR - Data Verification Portal") as demo:
    # Zain Branded Banner Header
    gr.HTML(
        """
        <div class="zain-header">
            <h1>Zain HR Portal</h1>
            <p>Data Sheet Verification & Management System</p>
        </div>
        """
    )
    
    # User status bar and logout button
    with gr.Row(elem_classes=["user-info-row"]):
        who_md = gr.Markdown()
        logout_btn = gr.Button("Log out", link="/logout", scale=0, variant="secondary")

    with gr.Tab("Upload"):
        files = gr.File(
            label="Choose CSV, XLSX or XLS files",
            file_count="multiple",
            file_types=[".csv", ".xlsx", ".xls"],
            type="filepath",
        )
        go = gr.Button("Upload and Verify File", variant="primary")
        result = gr.Markdown()

    with gr.Tab("Tables"):
        note_tables = gr.Markdown()
        table_pick = gr.Dropdown(label="Table", choices=[])
        table_view = gr.Dataframe(interactive=False)
        refresh_tables = gr.Button("Refresh", variant="secondary")

    with gr.Tab("Change log"):
        note_log = gr.Markdown()
        log_view = gr.Dataframe(interactive=False)
        refresh_log = gr.Button("Refresh", variant="secondary")

    # Admin Management Tab (Hidden by default for non-admins)
    with gr.Tab("Users", visible=False) as tab_users:
        users_view = gr.Dataframe(interactive=False)
        gr.Markdown("### Add or Modify User\n*Leave password empty to keep existing password.*")
        u_name = gr.Textbox(label="NT Username")
        u_pass = gr.Textbox(label="Password (min. 8 characters)", type="password")
        u_admin = gr.Checkbox(label="Grant Admin Rights")
        save_btn = gr.Button("Save User", variant="primary")
        
        gr.Markdown("---")
        gr.Markdown("### Delete User")
        d_name = gr.Textbox(label="NT Username to Delete")
        del_btn = gr.Button("Delete User", variant="stop")
        user_msg = gr.Markdown()

    # Event Bindings
    go.click(upload_files, files, [result, files]).then(show_log, None, log_view).then(
        list_tables, None, table_pick
    )
    table_pick.change(show_table, table_pick, table_view)
    refresh_tables.click(list_tables, None, table_pick)
    refresh_log.click(show_log, None, log_view)
    save_btn.click(save_user_ui, [u_name, u_pass, u_admin], [user_msg, users_view, u_pass]).then(
        show_log, None, log_view
    )
    del_btn.click(delete_user_ui, d_name, [user_msg, users_view]).then(show_log, None, log_view)

    # Load initial user state and tables
    demo.load(whoami, None, who_md)
    demo.load(notices, None, [note_tables, note_log])
    demo.load(role_tabs, None, tab_users)
    demo.load(show_log, None, log_view)
    demo.load(list_tables, None, table_pick)
    demo.load(show_users, None, users_view)
# =============== COPY THIS PART ===============
if __name__ == "__main__":
    demo.launch(
        auth=checks.verify_login,
        theme=zain_theme,
        css=custom_css,
    )
