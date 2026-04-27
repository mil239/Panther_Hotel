import sqlite3
from flask import Flask, render_template, request, jsonify, g
from datetime import datetime

app = Flask(__name__)
DATABASE = 'panther.db'

# Database Help
def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row 
    return g.db

@app.teardown_appcontext
def close_db(error):
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db():
    # Creates tables and room data if nonexistant
    db = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row
    cursor = db.cursor()

    # Table for rooms
    cursor.execute('''
        CREATE TABLE IF NOT EXIST rooms (
                id          INTERGER PRIMARY KEY AUTOINCREMENT,
                name        TEXT NOT NULL,
                type        TEXT NOT NULL,
                price       INTEGER NOT NULL,
                capacity    INTEGER NOT NULL,  
                size        TEXT NOT NULL,
                description TEXT NOT NULL,
                amenities   TEXT NOT NULL
        )
    ''')

    # Table for reservations
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS revervations (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    guest_name  TEXT NOT NULL,
                   check_in     Text NOT NULL,
                   check_out    TEXT NOT NULL,
                   room_type    TEXT NOT NULL,
                   nights       INTEGER NOT NULL,
                   created_at   TEXT NOT NULL   
        )
    ''')

    # For if the table is empty
    count = cursor.execute('SELECT COUNT(*) FROM rooms').fetchone()[0]
    if count == 0:
        seed_rooms = [
            # Room 1
            ('Shadow Suite',    'suite',    420, 2, '75 m²',
             'Drapped in obsidian and gold. Floor-to-ceiling windows revealing the city skyline, with a private terrace to invite the night in.', 
             'King Bed, Private Terrace, Mini Bar, City View'),
            # Room 2 
            ('Panther Deluxe',  'deluxe',   250, 2, '45 m²',
             'Bold geometric patterns meet plush comfort. Commanding, yet deeply restful.', 
             'King Bed, Work Desk, Mini Bar, City View'),
            # Room 3
            ('Twin Claw',   'standard',     180, 3, '30 m²',
             'Two sleek twin beds set within a bold, graphic space.',
             'Twin Beds, Walk-in Shower, Smart TV, Work Desk'),
            # Room 4
            ('The Apex Penthouse',  'penthouse',    1000, 5, '150 m²',
             'The pinnacle of Panther Hotel. Warparound views and private chef access.',
             '2 King Beds, Private Pool, Full Kitchen, Dining Room, Butler 24/7, Panoramic View'),
            # Room 5
            ('Midnight Studio', 'standard', 100, 1, '25 m²',
             'Compact and considered. Exceptional bed, exceptional shower, exceptional silence',
             'Queen Bed, Rain Shower, Smart TV, Coffee Machine'),
        ]
        cursor.excutemany(
            'INSERT INTO rooms (name, type, price, capacity, size, description, amenities) VALUES (?,?,?,?,?,?,?)',
            seed_rooms
        )
    db.commit()
    db.close()
def row_to_dict(row):
    return(row)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/reservation')
def reservation():
    db = get_db()
    rooms = [row_to_dict(r)  for r in db.execute('SELECT * FROM rooms ORDER BY price').fetchall()]
    return render_template('reservation.html', rooms=rooms)

@app.route('/confirmation/<int:booking_id>')
def confirmation(booking_id):
    db = get_db()
    booking = db.execute('SELECT * FROM reservations WHERE id = ?', (booking_id,)).fetchone()
    if not booking:
        return "Reservation not found", 404
    return render_template('confirmation.html', booking=row_to_dict(booking))

@app.route('/manager')
def manager():
    return render_template('manager.html')

# API
@app.route('/api/rooms')
def get_rooms():
    db = get_db()
    rows = db.execute('SELECT * FROM rooms ORDER BY price').fetchall()
    rooms = []
    for r in rows:
        d = row_to_dict(r)
        d['amenities'] = d['amenities'].split(',')
        rooms.append(d)
    return jsonify(rooms)

@app.route('/api/reserve', methods = ['POST'])
def make_reservation():
    data = request.get_json()
    required = ['guest_name', 'check_in', 'check_out', 'room_type']
    for field in required:
        if not data.get(field):
            return jsonify({'error': f'Missing field: {field}'}), 400
        
        check_in_d = datetime.strptime(data['check_in'], '%Y-%m-%d').date()
        check_out_d = datetime.strptime(data['check_out'], '%Y-%m-%d').date()
        nights = (check_out_d - check_in_d).days
        if nights <= 0:
            return jsonify({'error':'Check-out must be after check-in'}), 400

        db = get_db()
        cursor = db.execute(
            'INSERT INTO reservations (guest_name, check_in, check_out, room_type, nights, created_at) VALUES (?,?,?,?,?,?)',
            (data['guest_name'], data['check_in'], data['check_out'],
             data['room_type'], nights, datetime.now().isoformat())
        )
        db.commit()

        booking = row_to_dict(db.execute('SELECT * FROM reservations WHERE id = ?', (cursor.lastrowid,)).fetchone())
        return jsonify(booking), 201
    
@app.route('/api/reservations')
def get_reservations():
    db = get_db()
    rows = db.execute('SELECT * FROM reservations ORDER BY id DESC').fetchall()
    return jsonify([row_to_dict(r) for r in rows])

# Running the page
if __name__ == '__main__': 
    init_db() 
    app.run(debug = True, port = 5000)
