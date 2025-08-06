import glob
from flask import Flask, render_template, request, redirect, url_for, flash, session
import os
import csv
from datetime import datetime
from werkzeug.utils import secure_filename
import pandas as pd
from flask import send_file
from flask import send_file
from analysis.topic_modeling import run_topic_modeling

from analysis.sentiment import analyze_sentiment

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'csv'}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)






def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

app = Flask(__name__)
app.secret_key = 'very_secret_key'  # Needed for flashing messages and sessions

ADMIN_PASSWORD = "admin123"   # You can change this to any secret password
DATA_FILE = os.path.join('data', 'feedback_data.csv')
os.makedirs('data', exist_ok=True)

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        password = request.form.get('password', '')
        if password == ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            flash('Welcome, Admin!', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Incorrect password.', 'danger')
            return render_template('admin_login.html')
    return render_template('admin_login.html')

@app.route('/admin/dashboard')
def admin_dashboard():
    if not session.get('admin_logged_in'):
        flash('Please log in as admin.', 'warning')
        return redirect(url_for('admin_login'))
    return render_template('admin_dashboard.html')







#ADMIN UPLOAD ROUTE
ALLOWED_EXTENSIONS = {'csv'}
REQUIRED_COLUMNS = ['feedback', 'Name', 'Course']

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/admin/upload', methods=['GET', 'POST'])
def upload():
    if not session.get('admin_logged_in'):
        flash('Please log in as admin.', 'warning')
        return redirect(url_for('admin_login'))

    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part.', 'danger')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash('No file selected.', 'danger')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            save_path = os.path.join(UPLOAD_FOLDER, filename)
            try:
                file.save(save_path)
                # --- Step 2: Check for required columns ---
                import pandas as pd
                df = pd.read_csv(save_path, encoding='utf-8')
                missing_cols = [col for col in REQUIRED_COLUMNS if col not in df.columns]
                if missing_cols:
                    os.remove(save_path)
                    flash(f"Upload failed: missing required column(s): {', '.join(missing_cols)}.", 'danger')
                    return redirect(request.url)
            except Exception as e:
                if os.path.exists(save_path):
                    os.remove(save_path)
                flash(f"Failed to process file: {str(e)}", 'danger')
                return redirect(request.url)
            flash('File uploaded and validated successfully!', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid file type. Only CSV allowed.', 'danger')
            return redirect(request.url)
    return render_template('upload.html')












@app.route('/admin/feedback')
def view_feedback():
    if not session.get('admin_logged_in'):
        flash('Please log in as admin.', 'warning')
        return redirect(url_for('admin_login'))
    # Read feedback data
    feedback_entries = []
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            for row in reader:
                feedback_entries.append(row)
    # Each row: [timestamp, student_name, course, feedback, source]
    return render_template('view_feedback.html', feedback_entries=feedback_entries)




@app.route('/admin/analysis')
def run_analysis():
    if not session.get('admin_logged_in'):
        flash('Please log in as admin.', 'warning')
        return redirect(url_for('admin_login'))
    feedback_entries = []
    results = []
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            for row in reader:
                feedback_entries.append(row)
        for row in feedback_entries:
            feedback_text = row[3]
            sentiment_label, sentiment_score = analyze_sentiment(feedback_text)
            results.append({
                "timestamp": row[0],
                "name": row[1],
                "course": row[2],
                "feedback": feedback_text,
                "source": row[4],
                "sentiment": sentiment_label,
                "score": sentiment_score
            })
        # Save analyzed results to a new CSV
        analyzed_df = pd.DataFrame(results)
        analyzed_df.to_csv(os.path.join('data', 'feedback_with_sentiment.csv'), index=False, encoding='utf-8')
        flash("Analysis complete and results saved!", "success")
    return render_template('results.html', results=results)



#download route on the Analysis Page
@app.route('/admin/download_analysis')
def download_analysis():
    if not session.get('admin_logged_in'):
        flash('Please log in as admin.', 'warning')
        return redirect(url_for('admin_login'))
    analysis_file = os.path.join('data', 'feedback_with_sentiment.csv')
    if not os.path.exists(analysis_file):
        flash("No analysis file found. Please run analysis first.", "danger")
        return redirect(url_for('run_analysis'))
    return send_file(analysis_file, as_attachment=True)



#Analyze Manual Feedback Only
@app.route('/admin/analysis/manual')
def run_manual_analysis():
    if not session.get('admin_logged_in'):
        flash('Please log in as admin.', 'warning')
        return redirect(url_for('admin_login'))
    feedback_entries = []
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            for row in reader:
                feedback_entries.append(row)
    results = []
    for row in feedback_entries:
        feedback_text = str(row[3])
        sentiment_label, sentiment_score = analyze_sentiment(feedback_text)
        results.append({
            "timestamp": row[0],
            "name": row[1],
            "course": row[2],
            "feedback": feedback_text,
            "source": "manual",
            "sentiment": sentiment_label,
            "score": sentiment_score
        })
    # Save analyzed manual feedback
    pd.DataFrame(results).to_csv(os.path.join('data', 'manual_feedback_with_sentiment.csv'), index=False, encoding='utf-8')
    flash("Manual feedback analysis complete.", "success")
    return render_template('results.html', results=results)



# Analyze Uploaded Datasets (Select a File)
@app.route('/admin/analysis/uploaded', methods=['GET', 'POST'])
def analyze_uploaded():
    if not session.get('admin_logged_in'):
        flash('Please log in as admin.', 'warning')
        return redirect(url_for('admin_login'))

    # List available upload files (in uploads/)
    upload_files = [os.path.basename(f) for f in glob.glob(os.path.join('uploads', '*.csv'))]
    results = []
    selected_file = None

    if request.method == 'POST':
        selected_file = request.form.get('csv_file')
        selected_path = os.path.join('uploads', selected_file)
        if selected_file and os.path.exists(selected_path):
            import pandas as pd
            df = pd.read_csv(selected_path, encoding='utf-8')
            # For your dataset, these are the right columns:
            # 'feedback', 'Name', 'Course', 'Year'
            if 'feedback' in df.columns:
                feedback_col = 'feedback'
            elif 'comment' in df.columns:
                feedback_col = 'comment'
            else:
                flash("No feedback/comment column found.", "danger")
                return redirect(request.url)
            for idx, row in df.iterrows():
                feedback_text = str(row[feedback_col])
                name = row.get('Name', '')
                course = row.get('Course', '')
                timestamp = row.get('Year', 'N/A')  # Or use another column if you prefer
                sentiment_label, sentiment_score = analyze_sentiment(feedback_text)
                results.append({
                    "timestamp": timestamp,
                    "name": name,
                    "course": course,
                    "feedback": feedback_text,
                    "source": selected_file,
                    "sentiment": sentiment_label,
                    "score": sentiment_score
                })
            # Save the analyzed results as a unique file
            if selected_file and results:
                analyzed_filename = f'analyzed_{selected_file}'
                analyzed_filepath = os.path.join('data', analyzed_filename)
                pd.DataFrame(results).to_csv(analyzed_filepath, index=False, encoding='utf-8')
            flash(f"Analysis of {selected_file} complete.", "success")
            print("CSV columns:", df.columns.tolist())

    return render_template('analyze_uploaded.html', upload_files=upload_files, results=results, selected_file=selected_file)









#Analyze All Feedback Combined (Optional Feature)
@app.route('/admin/analysis/combined')
def run_combined_analysis():
    if not session.get('admin_logged_in'):
        flash('Please log in as admin.', 'warning')
        return redirect(url_for('admin_login'))

    feedback_entries = []
    # 1. Manual feedback
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            for row in reader:
                feedback_entries.append(row)

    # 2. All uploads
    upload_files = glob.glob(os.path.join('uploads', '*.csv'))
    for file_path in upload_files:
        try:
            df = pd.read_csv(file_path, encoding='utf-8')
            if 'feedback' in df.columns:
                feedback_col = 'feedback'
            elif 'comment' in df.columns:
                feedback_col = 'comment'
            else:
                continue
            for idx, row in df.iterrows():
                feedback_entries.append([
                    row.get('timestamp', 'N/A'),
                    row.get('student_name', ''),
                    row.get('course', ''),
                    row[feedback_col],
                    os.path.basename(file_path)
                ])
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
            continue

    results = []
    for row in feedback_entries:
        feedback_text = str(row[3])
        sentiment_label, sentiment_score = analyze_sentiment(feedback_text)
        results.append({
            "timestamp": row[0],
            "name": row[1],
            "course": row[2],
            "feedback": feedback_text,
            "source": row[4],
            "sentiment": sentiment_label,
            "score": sentiment_score
        })
    pd.DataFrame(results).to_csv(os.path.join('data', 'all_feedback_with_sentiment.csv'), index=False, encoding='utf-8')
    flash("Combined analysis complete.", "success")
    return render_template('results.html', results=results)




#download uploaded data set analysed 
@app.route('/admin/download_uploaded_analysis/<filename>')
def download_uploaded_analysis(filename):
    if not session.get('admin_logged_in'):
        flash('Please log in as admin.', 'warning')
        return redirect(url_for('admin_login'))
    analyzed_filepath = os.path.join('data', f'analyzed_{filename}')
    if not os.path.exists(analyzed_filepath):
        flash('No analyzed file found for this upload.', 'danger')
        return redirect(url_for('analyze_uploaded'))
    return send_file(analyzed_filepath, as_attachment=True)


#download thematic analysis data set analysed 
@app.route('/admin/download_topic_analysis/<filename>')
def download_topic_analysis(filename):
    if not session.get('admin_logged_in'):
        flash('Please log in as admin.', 'warning')
        return redirect(url_for('admin_login'))
    topic_csv_path = os.path.join('data', f'topic_analysis_{filename}')
    if not os.path.exists(topic_csv_path):
        flash('No topic analysis file found for this upload.', 'danger')
        return redirect(url_for('run_uploaded_topic_analysis'))
    return send_file(topic_csv_path, as_attachment=True)










#Add a Route for Topic Analysis (Manual Feedback Example)
@app.route('/admin/topic_analysis/manual')
def run_manual_topic_analysis():
    if not session.get('admin_logged_in'):
        flash('Please log in as admin.', 'warning')
        return redirect(url_for('admin_login'))
    feedback_entries = []
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            for row in reader:
                feedback_entries.append(row)
    feedback_texts = [row[3] for row in feedback_entries if row[3].strip()]

    # 🟢 Require at least 5 entries for BERTopic
    if len(feedback_texts) < 5:
        flash("Not enough feedback entries for topic modeling. Please provide at least 5.", "danger")
        return redirect(url_for('admin_dashboard'))

    topic_model, topics, probs = run_topic_modeling(feedback_texts)
    topic_info = topic_model.get_topic_info()
    topic_keywords = {row['Topic']: row['Name'] for _, row in topic_info.iterrows() if row['Topic'] != -1}

    samples_by_topic = {}
    for idx, topic_num in enumerate(topics):
        if topic_num == -1:
            continue
        samples_by_topic.setdefault(topic_num, []).append(feedback_texts[idx])

    topic_results = []
    for topic_num, keywords in topic_keywords.items():
        samples = samples_by_topic.get(topic_num, [])[:3]
        topic_results.append({
            "topic_num": topic_num,
            "keywords": keywords,
            "sample_feedback": samples
        })

    return render_template('topic_results.html', topic_results=topic_results)




@app.route('/admin/topic_analysis/uploaded', methods=['GET', 'POST'])
def run_uploaded_topic_analysis():
    if not session.get('admin_logged_in'):
        flash('Please log in as admin.', 'warning')
        return redirect(url_for('admin_login'))

    upload_files = [os.path.basename(f) for f in glob.glob(os.path.join('uploads', '*.csv'))]
    topic_results = []
    selected_file = None

    if request.method == 'POST':
        selected_file = request.form.get('csv_file')
        selected_path = os.path.join('uploads', selected_file)
        if selected_file and os.path.exists(selected_path):
            import pandas as pd
            df = pd.read_csv(selected_path, encoding='utf-8')
            # For your format: feedback column is 'feedback'
            if 'feedback' in df.columns:
                feedback_col = 'feedback'
            elif 'comment' in df.columns:
                feedback_col = 'comment'
            else:
                flash("No feedback/comment column found.", "danger")
                return redirect(request.url)

            feedback_texts = [str(row[feedback_col]) for idx, row in df.iterrows() if str(row[feedback_col]).strip()]

            if len(feedback_texts) < 5:
                flash("Not enough feedback entries for topic modeling. Please provide at least 5.", "danger")
                return render_template('topic_uploaded.html', upload_files=upload_files, topic_results=[], selected_file=selected_file)

            # Run topic modeling
            from analysis.topic_modeling import run_topic_modeling
            topic_model, topics, probs = run_topic_modeling(feedback_texts)

            # Get topic info and organize for display
            topic_info = topic_model.get_topic_info()
            topic_keywords = {row['Topic']: row['Name'] for _, row in topic_info.iterrows() if row['Topic'] != -1}

            samples_by_topic = {}
            for idx, topic_num in enumerate(topics):
                if topic_num == -1:
                    continue
                samples_by_topic.setdefault(topic_num, []).append(feedback_texts[idx])

            topic_results = []
            for topic_num, keywords in topic_keywords.items():
                samples = samples_by_topic.get(topic_num, [])[:3]  # Show up to 3 samples per topic
                topic_results.append({
                    "topic_num": topic_num,
                    "keywords": keywords,
                    "sample_feedback": samples
                })

            # 🟢 SAVE TOPIC ANALYSIS CSV HERE:
            if selected_file and topic_results:
                topic_csv_filename = f'topic_analysis_{selected_file}'
                topic_csv_path = os.path.join('data', topic_csv_filename)
                topic_data = []
                for topic in topic_results:
                    topic_data.append({
                        "topic_num": topic["topic_num"],
                        "keywords": topic["keywords"],
                        "sample_feedback_1": topic["sample_feedback"][0] if len(topic["sample_feedback"]) > 0 else "",
                        "sample_feedback_2": topic["sample_feedback"][1] if len(topic["sample_feedback"]) > 1 else "",
                        "sample_feedback_3": topic["sample_feedback"][2] if len(topic["sample_feedback"]) > 2 else ""
                    })
                pd.DataFrame(topic_data).to_csv(topic_csv_path, index=False, encoding='utf-8')

    return render_template('topic_uploaded.html', upload_files=upload_files, topic_results=topic_results, selected_file=selected_file)












































@app.route('/logout')
def logout():
    session.pop('admin_logged_in', None)
    flash('Logged out.', 'info')
    return redirect(url_for('admin_login'))



# (Keep your student feedback route at '/')
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        student_name = request.form.get('student_name', '').strip()
        course = request.form.get('course', '').strip()
        feedback = request.form.get('feedback', '').strip()

        # Error handling and validation
        if not course or not feedback:
            flash("Course and Feedback fields cannot be empty.", "danger")
            return render_template('index.html')
        if len(feedback) < 10:
            flash("Feedback must be at least 10 characters.", "warning")
            return render_template('index.html')
        if len(feedback) > 1000:
            flash("Feedback is too long (max 1000 characters).", "warning")
            return render_template('index.html')

        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with open(DATA_FILE, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([timestamp, student_name, course, feedback, "manual"])
        flash('Thank you for your feedback!', 'success')
        return redirect(url_for('index'))
    return render_template('index.html')


if __name__ == '__main__':
    app.run(debug=True)
