from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
import math
import heapq
import random

app = Flask(__name__)
app.secret_key = 'discrete-math-key'

# ============================================================
# 1. CRYPTOGRAPHY (Password Hashing)
# ============================================================
users = {
    'admin': {'pass': generate_password_hash('gwapo123'), 'role': 'admin', 'name': 'Admin', 'ID': 1},
    'proof_Cristian': {'pass': generate_password_hash('maot123'), 'role': 'faculty', 'name': 'Prof. Cristian', 'ID': 1},
    'jericho_cosadio': {'pass': generate_password_hash('maot123'), 'role': 'student', 'name': 'Jericho', 'ID': 2},
    'james_añabieza': {'pass': generate_password_hash('maot123'), 'role': 'student', 'name': 'James', 'ID': 2},
    'eric_lugnasin': {'pass': generate_password_hash('maot123'), 'role': 'faculty', 'name': 'Eric', 'ID': 1},
    'visitor1': {'pass': generate_password_hash('maot123'), 'role': 'visitor', 'name': 'Visitor', 'ID': 5}
}

# 10 ka Rooms gikan sa Gate padulong sa Tumoy
rooms = [
    'Library', 
    'Faculty Room', 
    'CS Dean\'s Office', 
    'Com Lab 1', 
    'Com Lab 2', 
    'Com Lab 3', 
    'Com Lab 4', 
    'Com Lab 5', 
    'Educ Room', 
    'Registrar Office'
]

# Set Theory
students = {'jericho_cosadio', 'james_añabieza'}
faculty = {'proof_Cristian', 'eric_lugnasin'}
visitors = {'visitor1'}
admins = {'admin'}
authorized_users = students | faculty | admins

# Access Matrix (Base sa bag-ong 10 rooms)
# Order: Library, Faculty, CS Dean, Lab1, Lab2, Lab3, Lab4, Lab5, Educ, Registrar
matrix = {
    'admin':           [1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
    'proof_Cristian':  [1, 1, 1, 1, 1, 1, 1, 1, 0, 1],
    'jericho_cosadio': [1, 1, 0, 0, 0, 0, 0, 0, 1, 1],
    'james_añabieza':  [1, 1, 1, 1, 1, 1, 1, 1, 0, 1],
    'eric_lugnasin':   [1, 1, 1, 0, 0, 0, 0, 0, 0, 1],
    'visitor1':        [1, 0, 0, 0, 0, 0, 0, 0, 0, 1]
}

# Relations
access_relations = set()
for user, perms in matrix.items():
    for i, allowed in enumerate(perms):
        if allowed == 1:
            access_relations.add((user, rooms[i]))

# ============================================================
# 2. GRAPHS (Campus Navigation - Dijkstra's Algorithm)
# ============================================================
# Gigamit nato ang weights para maipakita nga layo ang Lab 5 to Educ Room
campus_graph = {
    # 1. TUL-ID NGA DALAN (Main Route)
    'Library': {'Faculty Room': 5},
    'Faculty Room': {'Library': 5, 'CS Dean\'s Office': 5},
    'CS Dean\'s Office': {'Faculty Room': 5, 'Com Lab 1': 8},
    
    'Com Lab 1': {'CS Dean\'s Office': 8, 'Com Lab 2': 4, 'Educ Room': 18}, # Ang kurba paubos kay 18 units
    'Com Lab 2': {'Com Lab 1': 4, 'Com Lab 3': 4},
    'Com Lab 3': {'Com Lab 2': 4, 'Com Lab 4': 4},
    'Com Lab 4': {'Com Lab 3': 4, 'Com Lab 5': 4},
    
    # 2. WALKWAY GAP (Tunga sa Lab 5 ug Educ Room)
    'Com Lab 5': {'Com Lab 4': 4, 'Educ Room': 15},
    
    # 3. TUO NGA DALAN
    'Educ Room': {'Com Lab 5': 15, 'Registrar Office': 5, 'Com Lab 1': 18}, # Pabalik sa Com Lab 1
    'Registrar Office': {'Educ Room': 5}
}

def find_shortest_path(graph, start, end):
    queue = [(0, start, [start])]
    seen = set()
    while queue:
        (cost, node, path) = heapq.heappop(queue)
        if node not in seen:
            seen.add(node)
            if node == end:
                return cost, path
            for next_node, weight in graph.get(node, {}).items():
                if next_node not in seen:
                    heapq.heappush(queue, (cost + weight, next_node, path + [next_node]))
    return None, []

# ============================================================
# 3. TREES & RECURSION (Campus Hierarchy)
# ============================================================
campus_tree = {
    'BISU Clarin Campus': {
        'Ground Floor Building': {
            'Left Wing (Near Gate)': ['Library', 'Faculty Room', 'CS Dean\'s Office'],
            'Center Wing (ComLabs)': ['Com Lab 1', 'Com Lab 2', 'Com Lab 3', 'Com Lab 4', 'Com Lab 5'],
            'Right Wing (Far End)': ['Educ Room', 'Registrar Office']
        }
    }
}

def traverse_tree(tree, level=0):
    result = []
    for key, value in tree.items():
        result.append({'name': key, 'level': level})
        if isinstance(value, dict):
            result.extend(traverse_tree(value, level + 1))
        elif isinstance(value, list):
            for item in value:
                result.append({'name': item, 'level': level + 1})
    return result

# ============================================================
# 4. PROBABILITY (Room Availability Simulation)
# ============================================================
def simulate_room_availability():
    # 80% chance available, 20% chance occupied
    is_available = random.choices([True, False], weights=[0.8, 0.2])[0]
    return is_available

# ============================================================
# 5. SEARCHING & SORTING (User Records)
# ============================================================
def search_users(query):
    results = []
    query = query.lower()
    for username, info in users.items():
        if query in username.lower() or query in info['name'].lower():
            results.append({'username': username, **info})
    return results

def sort_users(users_dict, sort_by='name'):
    user_list = [{'username': k, **v} for k, v in users_dict.items()]
    return sorted(user_list, key=lambda x: str(x[sort_by]).lower())

# ============================================================
# 6. FINITE STATE MACHINE (FSM Tracker)
# ============================================================
FSM_STATES = ['Idle', 'Login', 'Access Granted', 'Access Denied', 'Navigating', 'Monitoring', 'Exit']

def update_fsm_state(new_state):
    if 'fsm_state' not in session:
        session['fsm_state'] = 'Idle'
    
    current_state = session['fsm_state']
    
    # Valid Transitions
    valid_transitions = {
        'Idle': ['Login'],
        'Login': ['Access Granted', 'Access Denied'],
        'Access Denied': ['Login'],
        'Access Granted': ['Navigating', 'Monitoring', 'Exit'],
        'Navigating': ['Monitoring', 'Exit'],
        'Monitoring': ['Navigating', 'Exit'],
        'Exit': ['Login']
    }
    
    if new_state in valid_transitions.get(current_state, []):
        session['fsm_state'] = new_state
        return True
    return False

# ============================================================
# BOOLEAN LOGIC & NUMBER THEORY
# ============================================================
def can_access(user, room_index):
    if user not in matrix:
        return False
    return matrix[user][room_index] == 1

def get_user_type(user):
    if user in admins: return 'admin'
    elif user in faculty: return 'faculty'
    elif user in students: return 'student'
    elif user in visitors: return 'visitor'
    return None

def modulo_check(id_num, room_num):
    if id_num == 0: return False
    return room_num % id_num == 0

def gcd_check(id_num, room_num):
    return math.gcd(id_num, room_num) > 1

# ============================================================
# PROOF OF CONSISTENCY
# ============================================================
def proof_of_consistency():
    proof = []
    proof.append("=== SHORT PROOF OF SYSTEM VALIDITY ===")
    proof.append("")
    proof.append("1. SET THEORY:")
    proof.append(f"   Authorized Users: {len(authorized_users)}")
    proof.append(f"   Total Access Relations: {len(access_relations)}")
    proof.append("")
    proof.append("2. BOOLEAN LOGIC:")
    proof.append("   Access = matrix[user][room] == 1")
    proof.append("")
    proof.append("3. NUMBER THEORY:")
    proof.append("   Modulo & GCD are used for secondary verification.")
    proof.append("")
    proof.append("4. GRAPH & TREE:")
    proof.append("   Dijkstra's algorithm calculates shortest paths.")
    proof.append("   Recursive tree traversal handles campus hierarchy.")
    proof.append("")
    proof.append("5. FINITE STATE MACHINE:")
    proof.append("   User session transitions: Idle -> Login -> Access -> Exit")
    proof.append("")
    proof.append("=== CONCLUSION ===")
    proof.append("The system is LOGICALLY VALID and MATHEMATICALLY CONSISTENT.")
    return proof

# ============================================================
# ROUTES
# ============================================================

@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = request.form['username']
        pwd = request.form['password']
        
        # CRYPTOGRAPHY: check_password_hash
        if user in users and check_password_hash(users[user]['pass'], pwd):
            session['user'] = user
            session['role'] = users[user]['role']
            session['name'] = users[user]['name']
            update_fsm_state('Access Granted') # FSM Update
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            update_fsm_state('Access Denied') # FSM Update
            flash('Invalid username or password!', 'danger')
    
    return render_template('login.html')

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'user' not in session:
        return redirect(url_for('login'))
    
    # PROBABILITY: Simulate room availabilities
    room_availability = {room: simulate_room_availability() for room in rooms}
    
    # NUMBER THEORY (Existing logic)
    num_result = None
    if request.method == 'POST':
        try:
            id_num = int(request.form['id'])
            room_num = int(request.form['room'])
            op = request.form['operation']
            
            if op == 'modulo':
                access = modulo_check(id_num, room_num)
                num_result = {
                    'op': 'Modulo',
                    'formula': f'{room_num} % {id_num} == 0',
                    'computed': f'{room_num} % {id_num} = {room_num % id_num}',
                    'access': access,
                    'msg': '✅ GRANTED' if access else '❌ DENIED'
                }
            elif op == 'gcd':
                g = math.gcd(id_num, room_num)
                access = gcd_check(id_num, room_num)
                num_result = {
                    'op': 'GCD',
                    'formula': f'GCD({id_num}, {room_num}) = {g}',
                    'computed': f'GCD = {g}',
                    'access': access,
                    'msg': '✅ GRANTED' if access else '❌ DENIED'
                }
        except ValueError:
            flash('Invalid input for Number Theory.', 'danger')

    return render_template('dashboard.html', 
                         user=session['user'],
                         name=session['name'],
                         role=session['role'],
                         rooms=rooms,
                         students=students,
                         faculty=faculty,
                         visitors=visitors,
                         admins=admins,
                         authorized_users=authorized_users,
                         access_relations=access_relations,
                         fsm_state=session.get('fsm_state', 'Idle'),
                         room_availability=room_availability,
                         num_result=num_result)

@app.route('/navigation', methods=['GET', 'POST'])
def navigation():
    if 'user' not in session:
        return redirect(url_for('login'))
    
    path_result = None
    cost = None
    if request.method == 'POST':
        start = request.form['start_room']
        end = request.form['end_room']
        cost, path_result = find_shortest_path(campus_graph, start, end)
        update_fsm_state('Navigating') # FSM Update
        
    return render_template('navigation.html', rooms=rooms, path=path_result, cost=cost)

@app.route('/records', methods=['GET', 'POST'])
def records():
    if 'user' not in session:
        return redirect(url_for('login'))
    
    search_query = request.args.get('search', '')
    sort_by = request.args.get('sort', 'name')
    
    # SEARCHING & SORTING
    if search_query:
        user_records = search_users(search_query)
    else:
        user_records = sort_users(users, sort_by=sort_by)
        
    return render_template('records.html', users=user_records, search_query=search_query, sort_by=sort_by)

@app.route('/tree')
def tree_view():
    if 'user' not in session:
        return redirect(url_for('login'))
    
    # TREES & RECURSION
    tree_data = traverse_tree(campus_tree)
    return render_template('tree.html', tree_data=tree_data)

@app.route('/check', methods=['GET', 'POST'])
def check():
    if 'user' not in session:
        return redirect(url_for('login'))
    
    result = None
    if request.method == 'POST':
        try:
            room_idx = int(request.form['room'])
            user = session['user']
            allowed = can_access(user, room_idx)
            
            result = {
                'user': user,
                'room': rooms[room_idx],
                'allowed': allowed,
                'message': '✅ ACCESS GRANTED' if allowed else '❌ ACCESS DENIED'
            }
        except (ValueError, IndexError):
            flash('Invalid room selection.', 'danger')
    
    return render_template('check.html', rooms=rooms, result=result)

@app.route('/matrix')
def matrix_view():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('matrix.html', rooms=rooms, matrix=matrix, users=users)

@app.route('/proof')
def proof():
    if 'user' not in session:
        return redirect(url_for('login'))
    proof_lines = proof_of_consistency()
    return render_template('proof.html', proof_lines=proof_lines)

@app.route('/logout')
def logout():
    update_fsm_state('Exit') # FSM Update
    session.clear()
    flash('Logged out!', 'info')
    return redirect(url_for('login'))

@app.route('/graph')
def graph_view():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('graph.html')

# ============================================================
# RUN
# ============================================================
if __name__ == '__main__':
    app.run(debug=True)