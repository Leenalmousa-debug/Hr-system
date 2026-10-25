import html
import os

# To run locally not make it go through proxy 
os.environ["NO_PROXY"] = "127.0.0.1,localhost"
os.environ["no_proxy"] = "127.0.0.1,localhost"

import gradio as gr
import pandas as pd

import checks


# (new) Icons. The two trash-can files are written into an "icons" folder next to this file each time the app starts.
ICON_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icons")
os.makedirs(ICON_DIR, exist_ok=True)
_TRASH_SVG = ('<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" '
              'stroke="{c}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
              '<path d="M3 6h18"/><path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/>'
              '<path d="M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/><path d="M10 11v6"/><path d="M14 11v6"/></svg>')
for _name, _color in (("trash_red.svg", "#C62828"), ("trash_white.svg", "#FFFFFF")):
    with open(os.path.join(ICON_DIR, _name), "w", encoding="utf-8") as _f:
        _f.write(_TRASH_SVG.format(c=_color))
TRASH_ICON = os.path.join(ICON_DIR, "trash_red.svg")  # the trash can next to each user
TRASH_ICON_BLACK = os.path.join(ICON_DIR, "trash_red.svg")  # on the red "Yes, delete" button
WARN_SVG = ('<svg xmlns="http://www.w3.org/2000/svg" width="26" height="26" viewBox="0 0 24 24" fill="none" '
            'stroke="#B26A00" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="flex:none">'
            '<path d="M10.29 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>'
            '<path d="M12 9v4"/><path d="M12 17h.01"/></svg>')  # the warning triangle
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
/* Delete confirmation modal */
#delete-modal {
    position: fixed !important;
    top: 50% !important;
    left: 50% !important;
    transform: translate(-50%, -50%) !important;

    width: min(440px, calc(100vw - 32px)) !important;
    max-width: 440px !important;
    box-sizing: border-box !important;

    z-index: 99999 !important;
    background: var(--background-fill-primary) !important;
    border: 1px solid var(--border-color-primary) !important;
    border-radius: 16px !important;
    padding: 24px !important;

    box-shadow: 0 0 0 100vmax rgba(0, 0, 0, 0.60),
                0 12px 35px rgba(0, 0, 0, 0.25) !important;

    overflow: visible !important;
}

/* Prevent Gradio's internal containers from clipping modal content */
#delete-modal > *,
#delete-modal .wrap {
    min-width: 0 !important;
    max-width: 100% !important;
    box-sizing: border-box !important;
}

/* Modal heading */
.modal-head {
    display: flex;
    align-items: center;
    gap: 12px;
    font-size: 21px;
    font-weight: 700;
    color: #5C2D91;
    margin-bottom: 16px;
}

/* Modal message */
#delete-modal p {
    font-size: 15px;
    line-height: 1.6;
    overflow-wrap: anywhere;
    margin: 10px 0;
}

/* Keep the two action buttons visible side by side */
#delete-modal .row {
    display: flex !important;
    flex-direction: row !important;
    flex-wrap: nowrap !important;
    align-items: stretch !important;
    gap: 12px !important;
    margin-top: 24px !important;
    width: 100% !important;
}

#delete-modal .row > * {
    flex: 1 1 0 !important;
    min-width: 0 !important;
    width: 50% !important;
}

#delete-modal button {
    min-height: 46px !important;
    height: auto !important;
    white-space: normal !important;
    overflow-wrap: anywhere !important;
    padding: 10px 12px !important;
    font-size: 14px !important;
}

/* Warning message */
.note-warn {
    display: flex;
    align-items: flex-start;
    gap: 10px;
    padding: 10px 14px;
    margin: 8px 0;
    border-left: 4px solid #B26A00;
    background: rgba(178, 106, 0, 0.08);
    border-radius: 6px;
}

.user-row,
.user-head {
    align-items: center;
    border-bottom: 1px solid var(--border-color-primary);
    padding: 4px 0;
}

.user-head {
    font-weight: 600;
}

.trash-btn {
    min-width: 44px !important;
}

/* Hide Gradio footer */
footer {
    display: none !important;
}
"""

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


def user_rows(request: gr.Request):  # (new) the users list, without the password hashes
    if not _admin(request):
        return []
    return [[u, "admin" if a else "standard user", c] for u, a, c in checks.list_users()]  # (new) one entry per user, drawn as a row with a trash icon


def save_user_ui(username, password, make_admin, request: gr.Request):  # (new) add or update a user
    msg = checks.save_user(_user(request), username, password, make_admin)
    return msg, user_rows(request), ""  # "" clears the password box


def delete_warning_html(username):  # (new) the text inside the pop-up
    return (f'<div class="modal-head">{WARN_SVG}<span>Delete this user?</span></div>'
            f"<p>You are about to permanently delete <b>{html.escape(username)}</b>. This cannot be undone.</p>"
            "<p>They will no longer be able to sign in. Their past uploads stay in the change log.</p>")


def make_ask(username):  # (new) builds the function for one user's trash icon
    def ask(request: gr.Request):
        if not _admin(request):
            return "", gr.Group(visible=False), "", ""
        if username.lower() == (_user(request) or "").lower():
            return "", gr.Group(visible=False), "", "You cannot delete your own account."
        return username, gr.Group(visible=True), delete_warning_html(username), ""  # opens the pop-up
    return ask


def confirm_delete(username, request: gr.Request):  # (new) the "Yes, delete" button
    msg = checks.delete_user(_user(request), username) if username else "No user selected."
    return msg, user_rows(request), "", gr.Group(visible=False)


def cancel_delete():  # (new) the "Cancel" button
    return "", gr.Group(visible=False), "Deletion cancelled."


# Building the App UI
with gr.Blocks(title="Zain HR - Data Verification Portal") as demo:
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
        users_state = gr.State([])  # (new) the list of users, redrawn below whenever it changes

        @gr.render(inputs=users_state)
        def draw_users(rows):  # (new) one row per user: name, role, created, trash icon
            with gr.Row(elem_classes="user-head"):
                gr.HTML("Username")
                gr.HTML("Role")
                gr.HTML("Created")
                gr.HTML("", min_width=44, scale=0)
            if not rows:
                gr.HTML("No users to show.")
            for username, role, created in rows:
                with gr.Row(elem_classes="user-row"):
                    gr.HTML(html.escape(username))
                    gr.HTML(role)
                    gr.HTML(html.escape(str(created)))
                    trash = gr.Button(
    "",
    icon=TRASH_ICON_BLACK,
    size="sm",
    scale=0,
    min_width=44,
    elem_classes="trash-btn"
)
                    trash.click(make_ask(username), None, [pending_user, confirm_box, confirm_md, user_msg])

        gr.HTML(f'<div class="note-warn">{WARN_SVG}<span>Deleting a user is permanent and cannot be undone. '
                "Use the trash icon in a user's row. You will be asked to confirm first.</span></div>")  # (new)
        pending_user = gr.State("")  # (new) the user waiting for confirmation
        user_msg = gr.Markdown()
        gr.Markdown("**Add a user, or change an existing one** (leave the password empty to keep it)")
        u_name = gr.Textbox(label="Username")
        u_pass = gr.Textbox(label="Password (at least 8 characters)", type="password")
        u_admin = gr.Checkbox(label="Admin")
        save_btn = gr.Button("Save user", variant="primary")

    with gr.Group(visible=False, elem_id="delete-modal") as confirm_box:
        confirm_md = gr.HTML()

        with gr.Row(equal_height=True):
            confirm_btn = gr.Button(
                "Yes, delete",
                variant="stop",
                icon=TRASH_ICON_BLACK,
                scale=1,
                min_width=0
            )
            cancel_btn = gr.Button(
                "Cancel",
                variant="secondary",
                scale=1,
                min_width=0
            )
    go.click(upload_files, [files, template_pick], [result, files]).then(show_log, None, log_view).then(
        list_tables, None, table_pick
    )
    template_pick.change(template_details, template_pick, template_info)  # (new)
    table_pick.change(show_table, table_pick, table_view)
    refresh_tables.click(list_tables, None, table_pick)
    refresh_log.click(show_log, None, log_view)
    save_btn.click(save_user_ui, [u_name, u_pass, u_admin], [user_msg, users_state, u_pass]).then(
        show_log, None, log_view
    )
    confirm_btn.click(confirm_delete, pending_user, [user_msg, users_state, pending_user, confirm_box]).then(
        show_log, None, log_view
    )  # (new)
    cancel_btn.click(cancel_delete, None, [pending_user, confirm_box, user_msg])  # (new)

    demo.load(whoami, None, who_md)
    demo.load(list_templates_ui, None, template_pick)  # (new)
    demo.load(notices, None, [note_tables, note_log])
    demo.load(role_tabs, None, tab_users)
    demo.load(show_log, None, log_view)
    demo.load(list_tables, None, table_pick)
    demo.load(user_rows, None, users_state)

if __name__ == "__main__":
    demo.launch(
        auth=checks.verify_login,
        theme=zain_theme,
        css=custom_css,
        allowed_paths=[ICON_DIR],  # (new) lets the page load the trash-can icons
    )  # (new) logins are checked against the users table now