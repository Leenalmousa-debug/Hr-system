#import libraries
import html
import os
import gradio as gr
import pandas as pd

#import files
import checks

# So it runs locally and doesnt go through proxy
# set variables
os.environ["NO_PROXY"] = "127.0.0.1,localhost"
os.environ["no_proxy"] = "127.0.0.1,localhost"
ICON_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icons")
os.makedirs(ICON_DIR, exist_ok=True) # if it doesnt create one
# Draws the svg from scratch  using the path d as instructions 
_TRASH_SVG = ('<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" '
              'stroke="{c}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
              '<path d="M3 6h18"/><path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/>'
              '<path d="M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/><path d="M10 11v6"/><path d="M14 11v6"/></svg>')
_WARN_SVG = ('<svg xmlns="http://www.w3.org/2000/svg" width="26" height="26" viewBox="0 0 24 24" fill="none" '
            'stroke="#B26A00" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="flex:none">'
            '<path d="M10.29 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>'
            '<path d="M12 9v4"/><path d="M12 17h.01"/></svg>')  

# the reason the warning didnt need to get written into a file while the trashcan did is because the trashcan is written on a button which needs path while # the waring html page so it takes object
# write the drawing in the svg file
with open(os.path.join(ICON_DIR,"trash_red.svg"), "w", encoding="utf-8") as _f:
        _f.write(_TRASH_SVG.format(c="#C62828"))
TRASH_ICON = os.path.join(ICON_DIR, "trash_red.svg") 

STANDARD_NOTE = "You only see the tables you have uploaded to, and the changes made to them."  


#Theming and styling
zain_teal = gr.themes.Color(
    c50="#e6f7f7",
    c100="#b3e8e8",
    c200="#80d8d9",
    c300="#4dc9ca",
    c400="#1ab9bb",
    c500="#00A3A6",  
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
    c500="#5C2D91", 
    c600="#512780",
    c700="#43206a",
    c800="#351954",
    c900="#27123d",
    c950="#1a0c29",
)


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

custom_css = """

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


.user-info-row {
    margin-bottom: 15px;
    align-items: center;
}


.tabs div button.selected {
    border-bottom-color: #00A3A6 !important;
    color: #5C2D91 !important;
    font-weight: 600;
}

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

#delete-modal > *,
#delete-modal .wrap {
    min-width: 0 !important;
    max-width: 100% !important;
    box-sizing: border-box !important;
}


.modal-head {
    display: flex;
    align-items: center;
    gap: 12px;
    font-size: 21px;
    font-weight: 700;
    color: #5C2D91;
    margin-bottom: 16px;
}


#delete-modal p {
    font-size: 15px;
    line-height: 1.6;
    overflow-wrap: anywhere;
    margin: 10px 0;
}


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

footer {
    display: none !important;
}
"""
#checks users to fetch data to display appropriately

def _user(request): 
    return getattr(request, "username", None)

def _admin(request):
    return checks.is_admin(_user(request))

def whoami(request: gr.Request):  
    u = _user(request)
    if not u:
        return "Not signed in."
    return f"Signed in as **{u}** ({'admin' if checks.is_admin(u) else 'standard user'})."

def notices(request: gr.Request):  
    text = "" if _admin(request) else STANDARD_NOTE
    return text, text

def role_tabs(request: gr.Request):
    return gr.Tab(visible=_admin(request))


#upload files check 

def upload_files(paths, template, request: gr.Request):
    if not paths:
        return "Choose at least one file first.", None
    user = _user(request) or "unknown"
    conn = checks.connect() 
    parts = []
    try:
        for p in paths:
            path = p if isinstance(p, str) else p.name #we use both cause some vesions of gradio send str some object with str name
            name = os.path.basename(path) #only file name
            with open(path, "rb") as f:
               r = checks.handle_file(conn, f, name, user, template)
            if r["status"] == "rejected":
                problems = "\n".join(f"- {e}" for e in r["errors"])
                parts.append(f"**{name}: REJECTED.** Nothing was changed.\n{problems}")
            else:
                action = "new table created" if r["status"] == "created" else "table replaced"
                parts.append(f"**{name}: accepted**, {action}: {r['table']} ({r['rows']} rows).")
    finally:
        conn.close()
    return "\n\n".join(parts), None  # None to empty the file box

#show list of templates
def list_templates_ui(): 
    return gr.Dropdown(choices=checks.list_templates(), value=None) #means kept empty until user decides

# shows the user what the chosen template requires
def template_details(name):  
    if not name:
        return ""
    try:
        cols = checks.load_template(name)
    except Exception as e:
        return f"This template has a problem: {e}. Ask an administrator to fix it."
    rules = "No extra columns, no empty values and no duplicate rows."
    if len(cols) == 1:
        listing = ", ".join(f"`{c}` " for c,_ in cols[0][1])
        return f"**Required columns, in this order:** {listing}\n\n{rules}"
    lines = [f"- **Sheet `{s}`:** " + ", ".join(f"`{c}`" for c,_ in sc) for s, sc in cols]  
    return ("**This Excel file needs exactly these sheets** (any order):\n" + "\n".join(lines)
            + f"\n\nEach sheet: columns in this order. {rules}")

#show list of tables option
def list_tables(request: gr.Request):
    conn = checks.connect() # connect to db 
    names = [
        row[0]
	# the explaination for this is that the connection returns  this format [("employees",), ("payroll",)] so when taking row zero we take only the string
        for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' "
            "AND name NOT IN ('change_log', 'users') AND name NOT LIKE 'sqlite_%' ORDER BY name"          )
    ]

    conn.close()
    if not _admin(request):  # a standard user only sees the tables he/she has taken part in
        mine = checks.my_tables(_user(request))
        names = [n for n in names if n in mine]
    return gr.Dropdown(choices=names, value=names[0] if names else None)  #show the names and vlaue of first table if there are any tables

#show table content
def show_table(name, request: gr.Request):
    if not name:
        return pd.DataFrame()
    if not _admin(request) and name not in checks.my_tables(_user(request)): 
        return pd.DataFrame()
    conn = checks.connect()
    df = pd.read_sql_query(f"SELECT * FROM {checks.q(name)}", conn) # we use checks.q to avoid sql injection
    conn.close()
    return df

#show logs
def show_log(request: gr.Request):
    conn = checks.connect()
    if _admin(request):
        df = pd.read_sql_query("SELECT * FROM change_log ORDER BY id DESC", conn)
    else:
        mine = checks.my_tables(_user(request) or "")
        marks = ",".join("?" * len(mine))
        sql = "SELECT * FROM change_log WHERE action NOT LIKE 'USER_%' AND (user = ? COLLATE NOCASE"
        sql += f" OR table_name IN ({marks})" if mine else "" # ifi do have tables then i have marks then  then i want to make sure table in marks
        sql += ") ORDER BY id DESC"
        df = pd.read_sql_query(sql, conn, params=[_user(request) or ""] + mine)
	# the query chooses the action isnt usersomething and the user is the current user ( here and later in marks the query will have placeholders that will be filled later on the reason is that i cant put mine directly to the sql statemnet as a variable
	
    conn.close()
    return df


#show users 
def user_rows(request: gr.Request):      
    if not _admin(request):
        return []
    return [[u, "admin" if a else "standard user", c] for u, a, c in checks.list_users()]  


def save_user_ui(username, password, make_admin, request: gr.Request):  # (new) add or update a user
    msg = checks.save_user(_user(request), username, password, make_admin)
    return msg, user_rows(request), ""  # "" clears the password box


def delete_warning_html(username):  
    return (f'<div class="modal-head">{_WARN_SVG}<span>Delete this user?</span></div>'
            f"<p>You are about to permanently delete <b>{html.escape(username)}</b>. This cannot be undone.</p>"
            "<p>They will no longer be able to sign in. Their past uploads stay in the change log.</p>")

#deletion of users this is a function of a function meaning it is set to be tied to a button when triggered it is executed 
def make_ask(username): 
    def ask(request: gr.Request):
        if not _admin(request):
            return "", gr.Group(visible=False), "", ""
        if username.lower() == (_user(request) or "").lower():
            return "", gr.Group(visible=False), "", "You cannot delete your own account."
        return username, gr.Group(visible=True), delete_warning_html(username), "" 
    return ask

def confirm_delete(username, request: gr.Request):  
    msg = checks.delete_user(_user(request), username) if username else "No user selected."
    return msg, user_rows(request), "", gr.Group(visible=False)


def cancel_delete():  # (new) the "Cancel" button
    return "", gr.Group(visible=False), "Deletion cancelled."


# App UI
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
        logout_btn = gr.Button("Log out", link="/logout", scale=0)  
    with gr.Tab("Upload"):
        template_pick = gr.Dropdown(label="Template", choices=[], info="Choose the template your file follows")  # (new)
        template_info = gr.Markdown()  
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
    with gr.Tab("Users", visible=False) as tab_users:  
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
    icon=TRASH_ICON,
    size="sm",
    scale=0,
    min_width=44,
    elem_classes="trash-btn"
)
                    trash.click(make_ask(username), None, [pending_user, confirm_box, confirm_md, user_msg])

        gr.HTML(f'<div class="note-warn">{_WARN_SVG}<span>Deleting a user is permanent and cannot be undone. '
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
                icon=TRASH_ICON,
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
    template_pick.change(template_details, template_pick, template_info)  
    table_pick.change(show_table, table_pick, table_view)
    refresh_tables.click(list_tables, None, table_pick)
    refresh_log.click(show_log, None, log_view)
    save_btn.click(save_user_ui, [u_name, u_pass, u_admin], [user_msg, users_state, u_pass]).then(
        show_log, None, log_view
    )
    confirm_btn.click(confirm_delete, pending_user, [user_msg, users_state, pending_user, confirm_box]).then(
        show_log, None, log_view
    )  # (new)
    cancel_btn.click(cancel_delete, None, [pending_user, confirm_box, user_msg]) 

    demo.load(whoami, None, who_md)
    demo.load(list_templates_ui, None, template_pick)  
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
        allowed_paths=[ICON_DIR],      )  