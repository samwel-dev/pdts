import os
import sqlite3
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

DB_FILE = 'pdts.db'

APP_VERSION = '1.0.0'
SCHEMA_VERSION = '1'

def init_db():
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS stations (
                        station_id TEXT PRIMARY KEY,
                        station_code TEXT UNIQUE,
                        station_name TEXT,
                        sub_county TEXT,
                        county TEXT,
                        region TEXT)''')

        conn.execute('''CREATE TABLE IF NOT EXISTS logs (
                        ref TEXT PRIMARY KEY,
                        station_id TEXT, date TEXT,
                        offence_category TEXT, offence_detail TEXT, other_specify TEXT,
                        value INTEGER, exact_age INTEGER, age_band TEXT,
                        gender TEXT, vulnerability TEXT, sub_county TEXT,
                        offender_behaviour TEXT, prior_history TEXT, offender_willingness TEXT,
                        complainant_willingness TEXT,
                        route TEXT, kind TEXT, ob TEXT, desc TEXT,
                        follow_up_date TEXT, officer TEXT, party_details TEXT, resolution_notes TEXT,
                        created_at TEXT, resolved_at TEXT, override_note TEXT,
                        anonymous_informant TEXT)''')

        for col in ['officer','party_details','resolution_notes','gender','vulnerability',
                    'sub_county','offender_behaviour','prior_history','offender_willingness',
                    'other_specify','station_id','offence_category','created_at','resolved_at',
                    'override_note','anonymous_informant','complainant_willingness']:
            try:
                conn.execute(f'ALTER TABLE logs ADD COLUMN {col} TEXT')
            except sqlite3.OperationalError:
                pass

        conn.execute('''CREATE TABLE IF NOT EXISTS audit (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        ref TEXT, action TEXT, detail TEXT, timestamp TEXT)''')

        conn.execute('''CREATE TABLE IF NOT EXISTS schema_version (
                        id INTEGER PRIMARY KEY CHECK (id = 1),
                        version TEXT,
                        set_at TEXT)''')
        row = conn.execute('SELECT version FROM schema_version WHERE id = 1').fetchone()
        if row is None:
            conn.execute('INSERT INTO schema_version (id, version, set_at) VALUES (1, ?, ?)',
                         (SCHEMA_VERSION, __import__('datetime').datetime.now().isoformat()))
        elif row[0] != SCHEMA_VERSION:
            print(f"WARNING: database schema version {row[0]} differs from app schema {SCHEMA_VERSION}")

        cur = conn.execute('SELECT COUNT(*) FROM stations')
        if cur.fetchone()[0] == 0:
            stations = [
                ('BGM001', 'BGM', 'Bungoma Main Police Station', 'Bungoma Central', 'Bungoma', 'Western'),
                ('NRB001', 'NRB', 'Nairobi Central Police Station', 'Nairobi Central', 'Nairobi', 'Nairobi'),
                ('MSA001', 'MSA', 'Mombasa Central Police Station', 'Mvita', 'Mombasa', 'Coast'),
                ('KSM001', 'KSM', 'Kisumu Central Police Station', 'Kisumu Central', 'Kisumu', 'Nyanza'),
                ('NKU001', 'NKU', 'Nakuru Central Police Station', 'Nakuru East', 'Nakuru', 'Rift Valley'),
                ('ELD001', 'ELD', 'Eldoret Police Station', 'Eldoret Central', 'Uasin Gishu', 'Rift Valley'),
                ('THK001', 'THK', 'Thika Police Station', 'Thika Town', 'Kiambu', 'Central'),
                ('NYR001', 'NYR', 'Nyeri Central Police Station', 'Nyeri Central', 'Nyeri', 'Central'),
                ('KSI001', 'KSI', 'Kisii Central Police Station', 'Kisii Central', 'Kisii', 'Nyanza'),
                ('MKS001', 'MKS', 'Machakos Police Station', 'Machakos Town', 'Machakos', 'Eastern'),
            ]
            conn.executemany('INSERT INTO stations VALUES (?,?,?,?,?,?)', stations)

init_db()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/stations', methods=['GET'])
def get_stations():
    with sqlite3.connect(DB_FILE) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute('SELECT * FROM stations ORDER BY station_name').fetchall()
    return jsonify([dict(row) for row in rows])

@app.route('/api/records', methods=['GET'])
def get_records():
    with sqlite3.connect(DB_FILE) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute('SELECT * FROM logs ORDER BY created_at DESC, ref DESC').fetchall()
    return jsonify([dict(row) for row in rows])

@app.route('/api/records', methods=['POST'])
def add_record():
    data = request.json
    try:
        with sqlite3.connect(DB_FILE) as conn:
            conn.execute('''INSERT INTO logs VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
                         (data['ref'], data.get('station_id',''), data['date'],
                          data.get('offence_category',''), data.get('offence_detail',''),
                          data.get('other_specify',''), data['value'],
                          data.get('exact_age', 0), data.get('age_band',''),
                          data.get('gender',''), data.get('vulnerability',''),
                          data.get('sub_county',''), data.get('offender_behaviour',''),
                          data.get('prior_history',''), data.get('offender_willingness',''),
                          data.get('complainant_willingness',''),
                          data['route'], data['kind'], data['ob'], data['desc'],
                          data.get('follow_up_date',''), data.get('officer',''),
                          data.get('party_details','[]'), data.get('resolution_notes',''),
                          data.get('created_at', ''), data.get('resolved_at', ''),
                          data.get('override_note', ''), data.get('anonymous_informant', '')))
            conn.execute('INSERT INTO audit (ref, action, detail, timestamp) VALUES (?,?,?,?)',
                         (data['ref'], 'CREATED', data['route'], data.get('created_at', '')))
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 400

@app.route('/api/records/<ref>', methods=['PUT'])
def update_record(ref):
    data = request.json
    try:
        with sqlite3.connect(DB_FILE) as conn:
            conn.execute('UPDATE logs SET resolution_notes = ?, resolved_at = ? WHERE ref = ?',
                         (data.get('resolution_notes',''), data.get('resolved_at',''), ref))
            conn.execute('INSERT INTO audit (ref, action, detail, timestamp) VALUES (?,?,?,?)',
                         (ref, data.get('action','UPDATE'), data.get('resolution_notes',''), data.get('resolved_at','')))
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 400

@app.route('/api/save_file', methods=['POST'])
def save_file():
    import os as _os
    data = request.json or {}
    filename = _os.path.basename(str(data.get('filename', 'export.csv')))
    content = str(data.get('content', ''))
    # Try common Desktop locations, in order
    candidates = [
        _os.path.join(_os.path.expanduser('~'), 'OneDrive', 'Desktop'),
        _os.path.join(_os.path.expanduser('~'), 'Desktop'),
        _os.path.join(_os.environ.get('USERPROFILE', ''), 'OneDrive', 'Desktop'),
        _os.path.join(_os.environ.get('USERPROFILE', ''), 'Desktop'),
        _os.getcwd(),
    ]
    target_dir = next((p for p in candidates if p and _os.path.isdir(p)), _os.getcwd())
    path = _os.path.join(target_dir, filename)
    try:
        with open(path, 'w', encoding='utf-8', newline='') as f:
            f.write(content)
        return jsonify({'status': 'success', 'path': path})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/print_html', methods=['POST'])
def print_html_route():
    """Save the printable HTML to a temp file and open it in the default browser.
    This avoids the WebView2 print crash inside PyWebView."""
    import tempfile, webbrowser, os as _os
    data = request.json or {}
    body = str(data.get('html', ''))
    if not body:
        return jsonify({'status': 'error', 'message': 'Empty HTML'}), 400
    fd, path = tempfile.mkstemp(suffix='.html', prefix='pdts_print_')
    _os.close(fd)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(body)
    try:
        webbrowser.open('file:///' + path.replace('\\', '/'))
        return jsonify({'status': 'success', 'path': path})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/version', methods=['GET'])
def version():
    return jsonify({
        'app_version': APP_VERSION,
        'schema_version': SCHEMA_VERSION
    })

@app.route('/api/backup', methods=['POST'])
def backup_db():
    import shutil, datetime, os as _os
    ts = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M')
    base_dir = _os.path.dirname(_os.path.abspath(DB_FILE))
    name = f'pdts_backup_{ts}.db'
    target = _os.path.join(base_dir, name)
    try:
        shutil.copy2(DB_FILE, target)
        return jsonify({'status': 'success', 'path': target, 'size': _os.path.getsize(target)})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/records', methods=['DELETE'])
def clear_records():
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute('DELETE FROM logs')
        conn.execute('DELETE FROM audit')
    return jsonify({'status': 'success'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)