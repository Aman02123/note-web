# Flask Note App - Complete Fixed Version
# manage.py

import os
import secrets
from PIL import Image
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user

# Initialize Flask app
app = Flask(__name__)

# Configuration
app.secret_key = 'any_long_random_string_here_change_in_production'

# Database config
# Format: mysql://username:password@localhost/databasename
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:arjun2005@localhost/note_app'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# File upload configuration
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'}

# Session configuration
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['PERMANENT_SESSION_LIFETIME'] = 1800  # 30 minutes

# Initialize extensions
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'info'

# Create upload directory
# Define the UPLOAD_FOLDER explicitly if it's not in Config
if 'UPLOAD_FOLDER' not in app.config:
    app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static', 'uploads')

# Define allowed file extensions
if 'ALLOWED_EXTENSIONS' not in app.config:
    app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'}

# Now this will no longer throw a KeyError
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Database Models
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    notes = db.relationship('Note', backref='author', lazy=True, cascade='all, delete-orphan')
    
    def set_password(self, password):
        """Hash and store password securely"""
        self.password_hash = generate_password_hash(password)
        print(f"DEBUG: Setting password for user {self.username}")
        print(f"DEBUG: Generated hash: {self.password_hash[:50]}...")
    
    def check_password(self, password):
        """Verify password against stored hash"""
        print(f"DEBUG: Checking password for user {self.username}")
        print(f"DEBUG: Stored hash: {self.password_hash[:50]}...")
        print(f"DEBUG: Password provided: {password}")
        
        result = check_password_hash(self.password_hash, password)
        print(f"DEBUG: Password check result: {result}")
        return result
    
    def __repr__(self):
        return f'<User {self.username}>'

class Note(db.Model):
    __tablename__ = 'notes'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text)
    image_filename = db.Column(db.String(255))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Note {self.title}>'



@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Helper Functions
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def save_picture(form_picture, folder):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.root_path, 'static', folder, picture_fn)
    
    # Resize image
    output_size = (800, 800)
    img = Image.open(form_picture)
    
    # Convert RGBA to RGB if necessary
    if img.mode == 'RGBA':
        img = img.convert('RGB')
    
    img.thumbnail(output_size)
    img.save(picture_path, optimize=True, quality=85)
    
    return picture_fn

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('notes'))
    
    if request.method == 'POST':
        username = request.form['username'].strip()
        email = request.form['email'].strip().lower()
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        
        print(f"DEBUG: Registration attempt - Username: {username}, Email: {email}")
        
        # Validation
        if not username or len(username) < 3:
            flash('Username must be at least 3 characters long.', 'danger')
            return render_template('register.html')
        
        if not email or '@' not in email:
            flash('Please enter a valid email address.', 'danger')
            return render_template('register.html')
        
        if len(password) < 6:
            flash('Password must be at least 6 characters long.', 'danger')
            return render_template('register.html')
        
        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('register.html')
        
        # Check if user already exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists. Please choose a different one.', 'danger')
            return render_template('register.html')
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered. Please use a different email or login.', 'danger')
            return render_template('register.html')
        
        # Create new user
        user = User(username=username, email=email)
        user.set_password(password)  # This will print debug info
        
        try:
            db.session.add(user)
            db.session.commit()
            print(f"DEBUG: User {username} registered successfully")
            flash('Registration successful! You can now log in.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            print(f"DEBUG: Registration error: {e}")
            flash('Registration failed. Please try again.', 'danger')
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('notes'))
    
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']
        remember = bool(request.form.get('remember'))
        
        print(f"DEBUG: Login attempt - Username: {username}")
        print(f"DEBUG: Remember me: {remember}")
        
        # Find user by username OR email
        user = User.query.filter(
            db.or_(User.username == username, User.email == username)
        ).first()
        
        if user:
            print(f"DEBUG: User found in database: {user.username}")
            print(f"DEBUG: User ID: {user.id}")
            
            # Check password
            if user.check_password(password):  # This will print debug info
                login_user(user, remember=remember)
                next_page = request.args.get('next')
                print(f"DEBUG: Login successful for {user.username}")
                flash(f'Welcome back, {user.username}!', 'success')
                return redirect(next_page) if next_page else redirect(url_for('notes'))
            else:
                print(f"DEBUG: Password check failed for {user.username}")
                flash('Invalid username or password.', 'danger')
        else:
            print(f"DEBUG: No user found with username/email: {username}")
            # Check what users exist (for debugging)
            all_users = User.query.all()
            print(f"DEBUG: All users in database: {[u.username for u in all_users]}")
            flash('Invalid username or password.', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('index'))

@app.route('/notes')
@login_required
def notes():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    
    query = Note.query.filter_by(user_id=current_user.id)
    
    if search:
        query = query.filter(
            db.or_(
                Note.title.contains(search),
                Note.content.contains(search)
            )
        )
    
    notes = query.order_by(Note.updated_at.desc()).paginate(
        page=page, per_page=6, error_out=False
    )
    
    return render_template('notes.html', notes=notes, search=search)

@app.route('/add_note', methods=['POST'])
@login_required
def add_note():
    try:
        title = request.form.get('title', '').strip()
        content = request.form.get('content', '').strip()
        
        print(f"DEBUG: Add note attempt - Title: '{title}', Content length: {len(content)}")
        
        if not title:
            print("DEBUG: Title is missing")
            return jsonify({'success': False, 'message': 'Title is required'})
        
        note = Note(title=title, content=content, user_id=current_user.id)
        print(f"DEBUG: Created note object for user {current_user.id}")
        
        # Handle image upload
        if 'image' in request.files:
            file = request.files['image']
            print(f"DEBUG: Image file received: {file.filename}")
            
            if file and file.filename != '' and allowed_file(file.filename):
                try:
                    filename = save_picture(file, 'uploads')
                    note.image_filename = filename
                    print(f"DEBUG: Image saved as: {filename}")
                except Exception as e:
                    print(f"DEBUG: Image upload error: {e}")
                    return jsonify({'success': False, 'message': f'Error uploading image: {str(e)}'})
        
        # Save to database
        db.session.add(note)
        db.session.commit()
        
        print(f"DEBUG: Note saved successfully with ID: {note.id}")
        return jsonify({'success': True, 'message': 'Note added successfully'})
        
    except Exception as e:
        db.session.rollback()
        print(f"DEBUG: Add note error: {e}")
        return jsonify({'success': False, 'message': f'Error saving note: {str(e)}'})

@app.route('/get_note/<int:note_id>')
@login_required
def get_note(note_id):
    try:
        note = Note.query.filter_by(id=note_id, user_id=current_user.id).first()
        
        if not note:
            print(f"DEBUG: Note {note_id} not found for user {current_user.id}")
            return jsonify({'error': 'Note not found'}), 404
        
        note_data = {
            'id': note.id,
            'title': note.title,
            'content': note.content or '',
            'image_filename': note.image_filename,
            'created_at': note.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': note.updated_at.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        print(f"DEBUG: Retrieved note {note_id} successfully")
        return jsonify(note_data)
        
    except Exception as e:
        print(f"DEBUG: Get note error: {e}")
        return jsonify({'error': f'Error retrieving note: {str(e)}'}), 500

@app.route('/edit_note/<int:note_id>', methods=['POST'])
@login_required
def edit_note(note_id):
    try:
        note = Note.query.filter_by(id=note_id, user_id=current_user.id).first()
        
        if not note:
            print(f"DEBUG: Note {note_id} not found for user {current_user.id}")
            return jsonify({'success': False, 'message': 'Note not found'})
        
        title = request.form.get('title', '').strip()
        content = request.form.get('content', '').strip()
        
        print(f"DEBUG: Edit note {note_id} - Title: '{title}', Content length: {len(content)}")
        
        if not title:
            print("DEBUG: Title is missing")
            return jsonify({'success': False, 'message': 'Title is required'})
        
        note.title = title
        note.content = content
        
        # Handle image upload
        if 'image' in request.files:
            file = request.files['image']
            print(f"DEBUG: Image file received: {file.filename}")
            
            if file and file.filename != '' and allowed_file(file.filename):
                try:
                    # Delete old image if exists
                    if note.image_filename:
                        old_image_path = os.path.join(app.root_path, 'static', 'uploads', note.image_filename)
                        if os.path.exists(old_image_path):
                            os.remove(old_image_path)
                            print(f"DEBUG: Deleted old image: {note.image_filename}")
                    
                    filename = save_picture(file, 'uploads')
                    note.image_filename = filename
                    print(f"DEBUG: New image saved as: {filename}")
                except Exception as e:
                    print(f"DEBUG: Image upload error: {e}")
                    return jsonify({'success': False, 'message': f'Error uploading image: {str(e)}'})
        
        # Save to database
        db.session.commit()
        
        print(f"DEBUG: Note {note_id} updated successfully")
        return jsonify({'success': True, 'message': 'Note updated successfully'})
        
    except Exception as e:
        db.session.rollback()
        print(f"DEBUG: Edit note error: {e}")
        return jsonify({'success': False, 'message': f'Error updating note: {str(e)}'})

@app.route('/delete_note/<int:note_id>', methods=['POST'])
@login_required
def delete_note(note_id):
    try:
        note = Note.query.filter_by(id=note_id, user_id=current_user.id).first()
        
        if not note:
            print(f"DEBUG: Note {note_id} not found for user {current_user.id}")
            return jsonify({'success': False, 'message': 'Note not found'})
        
        # Delete associated image if exists
        if note.image_filename:
            image_path = os.path.join(app.root_path, 'static', 'uploads', note.image_filename)
            if os.path.exists(image_path):
                os.remove(image_path)
                print(f"DEBUG: Deleted image: {note.image_filename}")
        
        # Delete note from database
        db.session.delete(note)
        db.session.commit()
        
        print(f"DEBUG: Note {note_id} deleted successfully")
        return jsonify({'success': True, 'message': 'Note deleted successfully'})
        
    except Exception as e:
        db.session.rollback()
        print(f"DEBUG: Delete note error: {e}")
        return jsonify({'success': False, 'message': f'Error deleting note: {str(e)}'})

# Debug Routes (REMOVE IN PRODUCTION!)
@app.route('/debug/users')
def debug_users():
    if not app.debug:
        return "Debug mode only", 403
    
    users = User.query.all()
    user_info = []
    
    for user in users:
        user_info.append({
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'password_hash': user.password_hash[:50] + '...',
            'created_at': user.created_at,
            'note_count': len(user.notes)
        })
    
    return jsonify(user_info)

@app.route('/debug/test-password')
def test_password():
    if not app.debug:
        return "Debug mode only", 403
    
    username = request.args.get('username')
    password = request.args.get('password')
    
    if not username or not password:
        return "Need username and password parameters"
    
    user = User.query.filter_by(username=username).first()
    if not user:
        return f"User {username} not found"
    
    result = user.check_password(password)
    return f"Password check for {username}: {result}"

@app.route('/debug/test-add-note')
def test_add_note():
    if not app.debug:
        return "Debug mode only", 403
    
    if not current_user.is_authenticated:
        return "Please login first"
    
    # Test creating a note directly
    try:
        test_note = Note(
            title="Test Note",
            content="This is a test note created directly.",
            user_id=current_user.id
        )
        db.session.add(test_note)
        db.session.commit()
        
        return f"Test note created successfully with ID: {test_note.id}"
    except Exception as e:
        db.session.rollback()
        return f"Error creating test note: {e}"

@app.route('/debug/current-user')
def current_user_debug():
    if not app.debug:
        return "Debug mode only", 403
    
    if current_user.is_authenticated:
        return jsonify({
            'authenticated': True,
            'user_id': current_user.id,
            'username': current_user.username,
            'email': current_user.email
        })
    else:
        return jsonify({'authenticated': False})

@app.route('/debug/check-uploads')
def check_uploads():
    if not app.debug:
        return "Debug mode only", 403
    
    upload_path = os.path.join(app.root_path, 'static', 'uploads')
    
    info = {
        'upload_path': upload_path,
        'path_exists': os.path.exists(upload_path),
        'is_directory': os.path.isdir(upload_path) if os.path.exists(upload_path) else False,
        'permissions': oct(os.stat(upload_path).st_mode)[-3:] if os.path.exists(upload_path) else 'N/A'
    }
    
    try:
        if os.path.exists(upload_path):
            info['files'] = os.listdir(upload_path)
        else:
            os.makedirs(upload_path, exist_ok=True)
            info['created'] = True
    except Exception as e:
        info['error'] = str(e)
    
    return jsonify(info)

# Error Handlers
@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        print("DEBUG: Database tables created")
        
        # Print existing users for debugging
        users = User.query.all()
        print(f"DEBUG: Found {len(users)} users in database")
        for user in users:
            print(f"DEBUG: User - ID: {user.id}, Username: {user.username}, Email: {user.email}")
    
    app.run(debug=True, host='0.0.0.0', port=5000)