import os

# To run locally not make it go through proxy 
os.environ["NO_PROXY"] = "127.0.0.1,localhost"
os.environ["no_proxy"] = "127.0.0.1,localhost"

import gradio as gr
import pandas as pd

import checks

STANDARD_NOTE = "You only see the tables you have uploaded to, and the changes made to them."  # (new) shown to standard users
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



def _user(request):  # (new) the name of whoever is signed in, or None
    return getattr(request, "username", None)


def _admin(request):  # (new) True only if that person is an admin in the users table
    return checks.is_admin(_user(request))


def whoami(request: gr.Request):  # (new) the "Signed in as ..." line at the top of the page
    u = _user(request)
    if not u:
        return "Not signed in."
    return f"Signed in as **{u}** ({'admin' if checks.is_admin(u) else 'standard user'})."


def notices(request: gr.Request):  # (new) a short note for standard users on the Tables and Change log tabs
    text = "" if _admin(request) else STANDARD_NOTE
    return text, text


def role_tabs(request: gr.Request):  # (new) the Users tab is only shown to admins
    return gr.Tab(visible=_admin(request))

#=============== REPLACE THIS PART ===============
def upload_files(paths, template, request: gr.Request):
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
               r = checks.handle_file(conn, f, name, user, template)
            if r["status"] == "rejected":
                problems = "\n".join(f"- {e}" for e in r["errors"])
                parts.append(f"**{name}: REJECTED.** Nothing was changed.\n{problems}")
            else:
                what = "new table created" if r["status"] == "created" else "table replaced"
                parts.append(f"**{name}: accepted**, {what}: {r['table']} ({r['rows']} rows).")
    finally:
        conn.close()
    return "\n\n".join(parts), None  # None empties the file box

def list_templates_ui():  # (new) fills the template dropdown from the templates folder
    return gr.Dropdown(choices=checks.list_templates(), value=None)


def template_details(name):  # (new) shows the user what the chosen template requires
    if not name:
        return ""
    try:
        cols = checks.load_template(name)
    except Exception as e:
        return f"This template has a problem: {e}. Ask an administrator to fix it."
    rules = "No extra columns, no empty values and no duplicate rows."
    if len(cols) == 1:
        listing = ", ".join(f"`{c}` ({t})" for c, t in cols[0][1])
        return f"**Required columns, in this order:** {listing}\n\n{rules}"
    lines = [f"- **Sheet `{s}`:** " + ", ".join(f"`{c}` ({t})" for c, t in sc) for s, sc in cols]  # (new) several sheets
    return ("**This Excel file needs exactly these sheets** (any order):\n" + "\n".join(lines)
            + f"\n\nEach sheet: columns in this order. {rules}")


def list_tables(request: gr.Request):
    conn = checks.connect() # connect to db 
    names = [
        row[0]
        for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' "
            "AND name NOT IN ('change_log', 'users') AND name NOT LIKE 'sqlite_%' ORDER BY name"  # (new) users is hidden too
        )
    ]
#[("employees",), ("payroll",)]
#Each row is a tuple with a single value inside. The comma after "employees" is how Python writes a one-item tuple.
#What row[0] does
    conn.close()
    if not _admin(request):  # (new) a standard user only sees the tables he/she has taken part in
        mine = checks.my_tables(_user(request))
        names = [n for n in names if n in mine]
    return gr.Dropdown(choices=names, value=names[0] if names else None)  #show the names and vlaue of first table


def show_table(name, request: gr.Request):
    if not name:
        return pd.DataFrame()
    if not _admin(request) and name not in checks.my_tables(_user(request)):  # (new) standard users: own tables only
        return pd.DataFrame()
    conn = checks.connect()
    df = pd.read_sql_query(f"SELECT * FROM {checks.q(name)}", conn) # we use checks.q to avoid sql injection
    conn.close()
    return df


def show_log(request: gr.Request):
    conn = checks.connect()
    if _admin(request):
        df = pd.read_sql_query("SELECT * FROM change_log ORDER BY id DESC", conn)
    else:  # (new) standard users: their own entries, plus every change to the tables they take part in
        user = _user(request) or ""
        mine = checks.my_tables(user)
        marks = ",".join("?" * len(mine))
        sql = "SELECT * FROM change_log WHERE action NOT LIKE 'USER_%' AND (user = ? COLLATE NOCASE"
        sql += f" OR table_name IN ({marks})" if mine else ""
        sql += ") ORDER BY id DESC"
        df = pd.read_sql_query(sql, conn, params=[user] + mine)
    conn.close()
    return df


def show_users(request: gr.Request):  # (new) the users list, without the password hashes
    if not _admin(request):
        return pd.DataFrame()
    rows = [(u, "yes" if a else "no", c) for u, a, c in checks.list_users()]
    return pd.DataFrame(rows, columns=["username", "admin", "created_at"])


def save_user_ui(username, password, make_admin, request: gr.Request):  # (new) add or update a user
    msg = checks.save_user(_user(request), username, password, make_admin)
    return msg, show_users(request), ""  # "" clears the password box


def delete_user_ui(username, request: gr.Request):  # (new) delete a user
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
    

    with gr.Row():
        who_md = gr.Markdown()
        logout_btn = gr.Button("Log out", link="/logout", scale=0)  # (new) for everyone
    with gr.Tab("Upload"):
        template_pick = gr.Dropdown(label="Template", choices=[], info="Choose the template your file follows")  # (new)
        template_info = gr.Markdown()  # (new)
        files = gr.File(
            label="Choose CSV, XLSX or XLS files",
            file_count="multiple",
            file_types=[".csv", ".xlsx", ".xls"],
            type="filepath",
        )
        go = gr.Button("Upload", variant="primary")
        result = gr.Markdown()
    with gr.Tab("Tables"):
        note_tables = gr.Markdown()
        table_pick = gr.Dropdown(label="Table", choices=[])
        table_view = gr.Dataframe(interactive=False)
        refresh_tables = gr.Button("Refresh")
    with gr.Tab("Change log"):
        note_log = gr.Markdown()
        log_view = gr.Dataframe(interactive=False)
        refresh_log = gr.Button("Refresh")
    with gr.Tab("Users", visible=False) as tab_users:  # (new) hidden until we know the person is an admin
        users_view = gr.Dataframe(interactive=False)
        gr.Markdown("**Add a user, or change an existing one** (leave the password empty to keep it)")
        u_name = gr.Textbox(label="Username")
        u_pass = gr.Textbox(label="Password (at least 8 characters)", type="password")
        u_admin = gr.Checkbox(label="Admin")
        save_btn = gr.Button("Save user", variant="primary")
        gr.Markdown("**Delete a user**")
        d_name = gr.Textbox(label="Username to delete")
        del_btn = gr.Button("Delete user")
        user_msg = gr.Markdown()

    go.click(upload_files, [files, template_pick], [result, files]).then(show_log, None, log_view).then(
        list_tables, None, table_pick
    )
    template_pick.change(template_details, template_pick, template_info)  # (new)
    table_pick.change(show_table, table_pick, table_view)
    refresh_tables.click(list_tables, None, table_pick)
    refresh_log.click(show_log, None, log_view)
    save_btn.click(save_user_ui, [u_name, u_pass, u_admin], [user_msg, users_view, u_pass]).then(
        show_log, None, log_view
    )
    del_btn.click(delete_user_ui, d_name, [user_msg, users_view]).then(show_log, None, log_view)

    demo.load(whoami, None, who_md)
    demo.load(list_templates_ui, None, template_pick)  # (new)
    demo.load(notices, None, [note_tables, note_log])
    demo.load(role_tabs, None, tab_users)
    demo.load(show_log, None, log_view)
    demo.load(list_tables, None, table_pick)
    demo.load(show_users, None, users_view)

if __name__ == "__main__":
    demo.launch(
        auth=checks.verify_login,
        theme=zain_theme,
        css=custom_css,
    )  # (new) logins are checked against the users table now