import os
import socket
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_bcrypt import Bcrypt
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SECRET_KEY'] = 'your_secret_key_here_change_me_please_2025'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 8 * 1024 * 1024  # 8MB max upload

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# ─────────────────────────────────────────────────────────────────────────────
# MODELS
# ─────────────────────────────────────────────────────────────────────────────

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(10), nullable=False, default='user')  # 'admin' or 'user'

    def __repr__(self):
        return f"<User {self.username}>"

class Application(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    link = db.Column(db.String(500), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(80), nullable=True)
    official_rating = db.Column(db.Float, nullable=True)          # 0.0–5.0
    image_filename = db.Column(db.String(200), nullable=True)
    added_at = db.Column(db.DateTime, default=datetime.utcnow)
    fraud_status = db.Column(
        db.String(20),
        nullable=False,
        default='pending'
    )   # pending, safe, suspicious, scam

    def __repr__(self):
        return f"<Application {self.name}>"

class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    application_id = db.Column(db.Integer, db.ForeignKey('application.id'), nullable=False)
    review_text = db.Column(db.Text, nullable=False)
    ip_address = db.Column(db.String(50), nullable=False)
    is_fake = db.Column(db.Boolean, default=False)
    sentiment_score = db.Column(db.Float, nullable=True)
    sentiment_label = db.Column(db.String(10), nullable=True)

    user = db.relationship('User', backref=db.backref('reviews', lazy=True))
    application = db.relationship('Application', backref=db.backref('reviews', lazy=True))

    def __repr__(self):
        return f"<Review {self.id} by user {self.user_id}>"

class Feedback(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref=db.backref('feedbacks', lazy=True))

    def __repr__(self):
        return f"<Feedback {self.id}>"

# ─────────────────────────────────────────────────────────────────────────────
# USER LOADER
# ─────────────────────────────────────────────────────────────────────────────

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ─────────────────────────────────────────────────────────────────────────────
# ROUTES
# ─────────────────────────────────────────────────────────────────────────────

@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        role = request.form.get('role', 'user')

        if not username or not email or not password:
            flash('All fields are required.', 'danger')
            return redirect(url_for('register'))

        if User.query.filter_by(email=email).first():
            flash('Email already registered.', 'danger')
            return redirect(url_for('register'))

        if User.query.filter_by(username=username).first():
            flash('Username already taken.', 'danger')
            return redirect(url_for('register'))

        hashed_pw = bcrypt.generate_password_hash(password).decode('utf-8')
        new_user = User(username=username, email=email, password=hashed_pw, role=role)
        db.session.add(new_user)
        db.session.commit()

        flash('Account created successfully! Please log in.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()

        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password.', 'danger')

    return render_template('login.html')

@app.route('/dashboard')
@login_required
def dashboard():
    if current_user.role == 'admin':
        # ── Admin dashboard data ──   
        fake_reviews = Review.query.filter_by(is_fake=True)\
                           .order_by(Review.id.desc()).limit(10).all()
        
        recent_reviews = Review.query.order_by(Review.id.desc()).limit(6).all()
        
        recent_applications = Application.query.order_by(Application.added_at.desc()).limit(6).all()
        
        total_applications     = Application.query.count()
        suspicious_applications   = Application.query.filter_by(fraud_status='suspicious').count()
        total_reviews          = Review.query.count()
        flagged_fake_reviews   = Review.query.filter_by(is_fake=True).count()
        total_feedbacks        = Feedback.query.count()
        recent_feedbacks_count = Feedback.query.count()  # or .limit(5).count() if you want recent only

        return render_template(
            'admin_dashboard.html',
            fake_reviews=fake_reviews,
            recent_reviews=recent_reviews,
            recent_applications=recent_applications,
            total_applications=total_applications,
            suspicious_applications=suspicious_applications,
            total_reviews=total_reviews,
            flagged_fake_reviews=flagged_fake_reviews,
            total_feedbacks=total_feedbacks,
            recent_feedbacks_count=recent_feedbacks_count
        )

    # ── User dashboard ──────────────────────────────────────────────────────
    search_query = request.args.get('q', '').strip()

    query = Application.query

    if search_query:
        search_term = f"%{search_query}%"
        query = query.filter(
            (Application.name.ilike(search_term)) |
            (Application.description.ilike(search_term)) |
            (Application.category.ilike(search_term))
        )

    applications = query.all()

    for app in applications:
        valid_scores = [
            r.sentiment_score 
            for r in app.reviews 
            if r.sentiment_score is not None
        ]

        total_reviews = len(app.reviews)
        valid_count   = len(valid_scores)

        avg_score = sum(valid_scores) / valid_count if valid_count > 0 else 0.0

        app.average_sentiment_score = round(avg_score, 2)
        app.total_review_count      = total_reviews
        app.valid_score_count       = valid_count

    if not search_query:
        applications = sorted(
            applications,
            key=lambda x: x.average_sentiment_score,
            reverse=True
        )

    return render_template(
        'user_dashboard.html',
        applications=applications,
        search_query=search_query
    )


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

# ─────────────────────────────────────────────────────────────────────────────
# ADMIN APPLICATION CRUD
# ─────────────────────────────────────────────────────────────────────────────

@app.route('/admin/applications')
@login_required
def admin_applications():
    if current_user.role != 'admin':
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('dashboard'))

    applications = Application.query.order_by(Application.added_at.desc()).all()
    return render_template('admin_applications.html', applications=applications)

@app.route('/admin/add_application', methods=['GET', 'POST'])
@login_required
def add_application():
    if current_user.role != 'admin':
        flash('Unauthorized.', 'danger')
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        link = request.form.get('link', '').strip()
        description = request.form.get('description', '').strip()
        category = request.form.get('category') or None
        official_rating_str = request.form.get('official_rating')
        fraud_status = request.form.get('fraud_status', 'pending')
        image = request.files.get('image')

        if not name or not link or not description:
            flash('Name, link, and description are required.', 'danger')
            return redirect(url_for('add_application'))

        official_rating = None
        if official_rating_str:
            try:
                val = float(official_rating_str)
                if 0 <= val <= 5:
                    official_rating = val
            except ValueError:
                pass

        filename = None
        if image and image.filename != '':
            filename = secure_filename(image.filename)
            image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        new_app = Application(
            name=name,
            link=link,
            description=description,
            category=category,
            official_rating=official_rating,
            image_filename=filename,
            fraud_status=fraud_status
        )

        db.session.add(new_app)
        db.session.commit()
        flash('Application added successfully.', 'success')
        return redirect(url_for('admin_applications'))

    return render_template('add_application.html')

@app.route('/admin/edit_application/<int:app_id>', methods=['GET', 'POST'])
@login_required
def edit_application(app_id):
    if current_user.role != 'admin':
        flash('Unauthorized.', 'danger')
        return redirect(url_for('dashboard'))

    app_obj = Application.query.get_or_404(app_id)

    if request.method == 'POST':
        app_obj.name = request.form.get('name', '').strip()
        app_obj.link = request.form.get('link', '').strip()
        app_obj.description = request.form.get('description', '').strip()
        app_obj.category = request.form.get('category') or None

        rating_str = request.form.get('official_rating')
        if rating_str:
            try:
                val = float(rating_str)
                app_obj.official_rating = val if 0 <= val <= 5 else None
            except ValueError:
                app_obj.official_rating = None
        else:
            app_obj.official_rating = None

        app_obj.fraud_status = request.form.get('fraud_status', 'pending')

        image = request.files.get('image')
        if image and image.filename != '':
            filename = secure_filename(image.filename)
            image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            app_obj.image_filename = filename

        db.session.commit()
        flash('Application updated successfully.', 'success')
        return redirect(url_for('admin_applications'))

    return render_template('edit_application.html', application=app_obj)

@app.route('/admin/delete_application/<int:app_id>')
@login_required
def delete_application(app_id):
    if current_user.role != 'admin':
        flash('Unauthorized.', 'danger')
        return redirect(url_for('dashboard'))

    app_obj = Application.query.get_or_404(app_id)
    db.session.delete(app_obj)
    db.session.commit()
    flash('Application deleted.', 'success')
    return redirect(url_for('admin_applications'))

# ─────────────────────────────────────────────────────────────────────────────
# REVIEW & SENTIMENT (kept mostly original – only minor cleanup)
# ─────────────────────────────────────────────────────────────────────────────

from nltk.corpus import sentiwordnet as swn
from nltk.corpus import wordnet
from nltk import pos_tag, word_tokenize
from nltk.stem import WordNetLemmatizer

def penn_to_wordnet(tag):
    if tag.startswith('J'):
        return wordnet.ADJ
    elif tag.startswith('V'):
        return wordnet.VERB
    elif tag.startswith('N'):
        return wordnet.NOUN
    elif tag.startswith('R'):
        return wordnet.ADV
    return None

def get_sentiment_score(text):
    lemmatizer = WordNetLemmatizer()
    tokens = word_tokenize(text.lower())
    tagged = pos_tag(tokens)
    
    total_score = 0.0
    count = 0
    word_results = []

    print(f"\nAnalyzing text: \"{text}\"\n")

    for word, tag in tagged:
        wn_tag = penn_to_wordnet(tag)
        if not wn_tag:
            print(f"Word: '{word}' - POS tag '{tag}' not mapped to WordNet POS. Skipping.\n")
            continue

        lemma = lemmatizer.lemmatize(word, pos=wn_tag)
        synsets = list(swn.senti_synsets(lemma, wn_tag))
        if not synsets:
            print(f"Word: '{word}' (lemma: '{lemma}', POS: {wn_tag}) - No SentiWordNet synsets found. Skipping.\n")
            continue

        synset = synsets[0]  # First synset for the lemma+pos
        pos_score = synset.pos_score()
        neg_score = synset.neg_score()
        obj_score = synset.obj_score()
        score = pos_score - neg_score

        print(f"Word: '{word}' (lemma: '{lemma}', POS: {wn_tag})")
        print(f"  Synset: {synset.synset.name()}")
        print(f"    Pos Score: {pos_score}")
        print(f"    Neg Score: {neg_score}")
        print(f"    Obj Score: {obj_score}")
        print(f"    Word Sentiment (pos - neg): {score}\n")

        total_score += score
        count += 1
        word_results.append((word, synset.synset.name(), pos_score, neg_score, obj_score, score))

    avg_score = total_score / count if count else 0.0

    if avg_score > 0.05:
        label = "positive"
    elif avg_score < -0.05:
        label = "negative"
    else:
        label = "neutral"

    # Print final calculation table
    print("Final Calculation Table:")
    print(f"{'Word':<12} {'Synset':<25} {'PosScore':<10} {'NegScore':<10} {'ObjScore':<10} {'WordScore':<15}")
    print("-" * 85)
    for wr in word_results:
        word, synset_name, pos, neg, obj, wscore = wr
        print(f"{word:<12} {synset_name:<25} {pos:<10.2f} {neg:<10.2f} {obj:<10.2f} {wscore:<15.2f}")

    print(f"\nFinal Sentiment Score (average): {avg_score:.3f}")
    print(f"Final Sentiment Label: {label}\n")

    return round(avg_score, 3), label


@app.route('/review/<int:app_id>', methods=['GET'])
@login_required
def review_page(app_id):
    application = Application.query.get_or_404(app_id)
    reviews = Review.query.filter_by(application_id=app_id).all()
    return render_template('add_review.html', application=application, reviews=reviews)

@app.route('/add_review/<int:app_id>', methods=['POST'])
@login_required
def add_review(app_id):
    review_text = request.form.get('review', '').strip()

    if not review_text:
        flash('Review cannot be empty.', 'danger')
        return redirect(url_for('review_page', app_id=app_id))

    ip_address = "unknown"
    try:
        ip_address = socket.gethostbyname(socket.gethostname())
    except:
        pass

    score, label = get_sentiment_score(review_text)

    count = Review.query.filter_by(user_id=current_user.id, application_id=app_id).count()
    is_fake = count >= 3

    review = Review(
        user_id=current_user.id,
        application_id=app_id,
        review_text=review_text,
        ip_address=ip_address,
        sentiment_score=score,
        sentiment_label=label,
        is_fake=is_fake
    )
    db.session.add(review)
    db.session.commit()

    if is_fake:
        flash('Review submitted (marked as potentially fake - too many from this user).', 'warning')
    else:
        flash('Review submitted successfully.', 'success')

    return redirect(url_for('review_page', app_id=app_id))

@app.route('/admin/reviews')
@login_required
def admin_reviews():
    if current_user.role != 'admin':
        flash('Unauthorized.', 'danger')
        return redirect(url_for('dashboard'))

    reviews = Review.query.order_by(Review.id.desc()).all()
    return render_template('admin_reviews.html', reviews=reviews)

@app.route('/admin/delete_review/<int:review_id>')
@login_required
def delete_review(review_id):
    if current_user.role != 'admin':
        flash('Unauthorized.', 'danger')
        return redirect(url_for('dashboard'))

    review = Review.query.get_or_404(review_id)
    db.session.delete(review)
    db.session.commit()
    flash('Review deleted.', 'success')
    return redirect(url_for('admin_reviews'))

# ─────────────────────────────────────────────────────────────────────────────
# FEEDBACK – USER SUBMIT + ADMIN VIEW / DELETE
# ─────────────────────────────────────────────────────────────────────────────

@app.route('/feedback', methods=['POST'])
@login_required
def submit_feedback():
    message = request.form.get('message', '').strip()
    if not message:
        flash('Feedback message cannot be empty.', 'danger')
        return redirect(url_for('dashboard'))

    feedback = Feedback(
        user_id=current_user.id,
        message=message
    )
    db.session.add(feedback)
    db.session.commit()

    flash('Thank you! Your feedback has been submitted.', 'success')
    return redirect(url_for('dashboard'))


@app.route('/admin/feedbacks')
@login_required
def admin_view_feedbacks():
    if current_user.role != 'admin':
        flash('Access denied. Admins only.', 'danger')
        return redirect(url_for('dashboard'))

    feedbacks = Feedback.query.order_by(Feedback.created_at.desc()).all()
    return render_template('admin_feedbacks.html', feedbacks=feedbacks)


@app.route('/admin/delete_feedback/<int:feedback_id>', methods=['POST', 'GET'])
@login_required
def admin_delete_feedback(feedback_id):
    if current_user.role != 'admin':
        flash('Access denied. Admins only.', 'danger')
        return redirect(url_for('dashboard'))

    feedback = Feedback.query.get_or_404(feedback_id)

    if request.method == 'POST' or request.method == 'GET':  # allowing GET for simplicity (you can restrict to POST)
        db.session.delete(feedback)
        db.session.commit()
        flash('Feedback deleted successfully.', 'success')

    return redirect(url_for('admin_view_feedbacks'))

# ─────────────────────────────────────────────────────────────────────────────
# RUN
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=5000)


