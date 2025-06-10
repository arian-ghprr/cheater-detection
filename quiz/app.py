from flask import Flask, render_template, request, jsonify
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from scipy.stats import pearsonr
import numpy as np
from itertools import combinations
import json
import os
import pandas as pd
from datetime import datetime, timedelta

app = Flask(__name__)

# مسیر فایل دیتابیس
DB_FILE = 'users_data.json'

def load_users():
    if not os.path.exists(DB_FILE):
        return []
    with open(DB_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_user(user):
    users = load_users()
    users.append(user)
    with open(DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(users, f, ensure_ascii=False, indent=2)

def calculate_string_similarity(str1, str2):
    """Calculate the cosine similarity between two strings"""
    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform([str1, str2])
    return cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]

def calculate_lcs_length(str1, str2):
    """Calculate the length of the longest common subsequence"""
    m, n = len(str1), len(str2)
    dp = [[0] * (n + 1) for _ in range(m + 1)]

    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if str1[i-1] == str2[j-1]:
                dp[i][j] = dp[i-1][j-1] + 1
            else:
                dp[i][j] = max(dp[i-1][j], dp[i][j-1])

    return dp[m][n]

def find_lcs(str1, str2):
    """Find the longest common subsequence between two strings"""
    m, n = len(str1), len(str2)
    dp = [[0] * (n + 1) for _ in range(m + 1)]

    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if str1[i-1] == str2[j-1]:
                dp[i][j] = dp[i-1][j-1] + 1
            else:
                dp[i][j] = max(dp[i-1][j], dp[i][j-1])

    lcs = []
    i, j = m, n
    while i > 0 and j > 0:
        if str1[i-1] == str2[j-1]:
            lcs.append(str1[i-1])
            i -= 1
            j -= 1
        elif dp[i-1][j] > dp[i][j-1]:
            i -= 1
        else:
            j -= 1

    return ''.join(reversed(lcs))

@app.route('/')
def welcome():
    return render_template('welcome.html')

@app.route('/quiz')
def quiz():
    return render_template('quiz.html')

@app.route('/results')
def results():
    return render_template('results.html')

@app.route('/test-panel')
def test_panel():
    return render_template('test_panel.html')

@app.route('/api/analyze', methods=['POST'])
def analyze_answers():
    data = request.get_json()
    users = data.get('users', [])
    current_user = users[-1]

    users_with_answers = [user for user in users if user.get('answers')]

    if len(users_with_answers) < 2:
        return jsonify({
            'name': current_user.get('name'),
            'message': 'هنوز کاربر دیگری به سوالات پاسخ نداده است.',
            'has_comparison': False
        })

    analysis_results = {}
    questions = {
        'question1': 'نظر درباره هوش مصنوعی',
        'question2': 'چالش امنیت سایبری',
        'question3': 'آینده بلاکچین'
    }

    current_answers = current_user.get('answers', {})

    for q_id in questions.keys():
        current_answer = current_answers.get(q_id, '')
        other_users_analysis = []

        for other_user in users_with_answers:
            if other_user['id'] != current_user['id']:
                other_answer = other_user['answers'].get(q_id, '')

                if current_answer and other_answer:
                    cosine_sim = calculate_string_similarity(current_answer, other_answer)
                    lcs = find_lcs(current_answer, other_answer)
                    lcs_percentage = (len(lcs) / max(len(current_answer), len(other_answer))) * 100

                    other_users_analysis.append({
                        'user_name': other_user['name'],
                        'user_answer': other_answer,
                        'current_answer': current_answer,
                        'cosine_similarity': cosine_sim,
                        'lcs': lcs,
                        'lcs_percentage': lcs_percentage,
                        'duration': other_user.get('duration', None)
                    })

        if other_users_analysis:
            # فقط بیشترین شباهت را نگه دار
            max_sim = max(other_users_analysis, key=lambda a: a['cosine_similarity'])
            other_users_analysis = [max_sim]
            avg_cosine = sum(a['cosine_similarity'] for a in other_users_analysis) / len(other_users_analysis)
            avg_lcs = sum(a['lcs_percentage'] for a in other_users_analysis) / len(other_users_analysis)
            avg_similarity = (avg_cosine * 100 + avg_lcs) / 2

            analysis_results[q_id] = {
                'question_title': questions[q_id],
                'comparisons': other_users_analysis,
                'average_cosine': avg_cosine,
                'average_lcs': avg_lcs,
                'average_similarity': avg_similarity
            }

    # === تحلیل شباهت زمانی ===
    timing_similarities = []
    current_timing = current_user.get('timing', {})

    for other_user in users_with_answers:
        if other_user['id'] != current_user['id']:
            other_timing = other_user.get('timing', {})
            common_qs = set(current_timing.keys()).intersection(set(other_timing.keys()))

            if len(common_qs) >= 2:
                curr_times = [current_timing[q] for q in sorted(common_qs)]
                other_times = [other_timing[q] for q in sorted(common_qs)]

                corr, _ = pearsonr(curr_times, other_times)
                if corr > 0.95:
                    timing_similarities.append({
                        'user_name': other_user['name'],
                        'correlation': round(corr, 3),
                        'questions': list(common_qs)
                    })

    # محاسبه مجموع زمان صرف‌شده برای کاربر فعلی
    current_total_time = sum(current_user.get('timing', {}).values()) if current_user.get('timing') else 0
    # مجموع زمان سایر کاربران
    other_users_times = [
        {'name': user['name'], 'total_time': sum(user.get('timing', {}).values()) if user.get('timing') else 0}
        for user in users_with_answers if user['id'] != current_user['id']
    ]
    return jsonify({
        'name': current_user.get('name'),
        'analysis': analysis_results,
        'has_comparison': True,
        'total_users': len(users_with_answers),
        'suspicious_time_patterns': timing_similarities,
        'current_total_time': current_total_time,
        'other_users_times': other_users_times
    })

@app.route('/api/save_user', methods=['POST'])
def api_save_user():
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'message': 'داده‌ای ارسال نشده است.'}), 400
    try:
        # محاسبه فاصله زمانی بین ورود و ثبت پاسخ
        login_time = data.get('login_time')
        submit_time = data.get('submit_time')
        if login_time and submit_time:
            t1 = pd.to_datetime(login_time)
            t2 = pd.to_datetime(submit_time)
            duration = t2 - t1
            duration_str = str(duration).split('.')[0]  # فقط HH:MM:SS
            data['duration'] = duration_str
        save_user(data)
        return jsonify({'success': True, 'message': 'کاربر با موفقیت ذخیره شد.'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'خطا در ذخیره کاربر: {str(e)}'}), 500

@app.route('/api/clear_users', methods=['POST'])
def clear_users():
    try:
        with open(DB_FILE, 'w', encoding='utf-8') as f:
            json.dump([], f, ensure_ascii=False, indent=2)
        return jsonify({'success': True, 'message': 'اطلاعات کاربران با موفقیت پاک شد.'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'خطا در پاک‌سازی: {str(e)}'}), 500

@app.route('/api/test_data')
def api_test_data():
    test_data = {
        "Test for Bug": [
          {"qnumber": 1, "description": 0, "time_taken": 20},
          {"qnumber": 2, "description": None, "time_taken": 25},
          {"qnumber": 3, "description": "", "time_taken": 18}
        ],
        "Alice": [
          {"qnumber": 1, "description": "Photosynthesis uses sunlight to make food.", "time_taken": 20},
          {"qnumber": 2, "description": "Compiled languages run faster than interpreted.", "time_taken": 25},
          {"qnumber": 3, "description": "The Industrial Revolution began in Britain.", "time_taken": 18}
        ],
        "Bob": [
          {"qnumber": 1, "description": "Photosynthesis uses sunlight to create food.", "time_taken": 21},
          {"qnumber": 2, "description": "Compiled languages run quicker than interpreted.", "time_taken": 26},
          {"qnumber": 3, "description": "The Industrial Revolution started in Britain.", "time_taken": 19}
        ],
        "Charlie": [
          {"qnumber": 1, "description": "Photosynthesis uses sunlite to make food.", "time_taken": 22},
          {"qnumber": 2, "description": "Compiled languages run faster than interprted.", "time_taken": 24},
          {"qnumber": 3, "description": "The Industrial Revoluton began in Britain.", "time_taken": 20}
        ],
        "Dana": [
          {"qnumber": 1, "description": "Photosynthesis uses sunlight to create food.", "time_taken": 23},
          {"qnumber": 2, "description": "Compiled languages run faster than interprted.", "time_taken": 27},
          {"qnumber": 3, "description": "The French Revolution began in France.", "time_taken": 21}
        ],
        "Eve": [
          {"qnumber": 1, "description": "Photosynthesis uses sunlight to make foud.", "time_taken": 19},
          {"qnumber": 2, "description": "Compiled languages run faster than interpreted.", "time_taken": 23},
          {"qnumber": 3, "description": "The Industrial Revolution began in Britan.", "time_taken": 17}
        ],
        "Frank": [
          {"qnumber": 1, "description": "Respiration releases energy from glucose.", "time_taken": 24},
          {"qnumber": 2, "description": "Scripting languages are often interpreted.", "time_taken": 28},
          {"qnumber": 3, "description": "The Civil War occurred in America.", "time_taken": 22}
        ],
        "Amir": [
        {"qnumber": 1, "description": "Artificial intelligence is the simulation of human intelligence in machines.", "time_taken": 40},
        {"qnumber": 2, "description": "Machine learning is a subset of AI that involves training algorithms on data.", "time_taken": 50},
        {"qnumber": 3, "description": "Python is widely used for AI development due to its simplicity and libraries.", "time_taken": 30}
      ],
      "Kimia": [
        {"qnumber": 1, "description": "Artificial intelligence is the simulation of human intelligence in machines.", "time_taken": 42},
        {"qnumber": 2, "description": "Machine learning is a subset of AI that involves training algorithms on data.", "time_taken": 52},
        {"qnumber": 3, "description": "Python is widely used for AI development due to its simplicity and libraries.", "time_taken": 32}
      ],
      "Negar": [
        {"qnumber": 1, "description": "Quantum computing uses quantum bits to perform computations.", "time_taken": 35},
        {"qnumber": 2, "description": "Blockchain is a decentralized ledger technology.", "time_taken": 45},
        {"qnumber": 3, "description": "JavaScript is essential for web development.", "time_taken": 25}
      ],
      "Farshad": [
        {"qnumber": 1, "description": "Quantum computing uses quantum bits to perform computations.", "time_taken": 37},
        {"qnumber": 2, "description": "Blockchain is a decentralized ledger technology.", "time_taken": 47},
        {"qnumber": 3, "description": "JavaScript is essential for web development.", "time_taken": 27}
      ],
      "Arad": [
        {"qnumber": 1, "description": "Renewable energy sources include solar and wind power.", "time_taken": 38},
        {"qnumber": 2, "description": "Climate change is a pressing global issue.", "time_taken": 48},
        {"qnumber": 3, "description": "C++ is used for high-performance applications.", "time_taken": 28}
      ],
      "Bita": [
        {"qnumber": 1, "description": "Renewable energy sources include solar and wind power.", "time_taken": 40},
        {"qnumber": 2, "description": "The internet is a global network of computers.", "time_taken": 50},
        {"qnumber": 3, "description": "HTML is used for creating web pages.", "time_taken": 30}
      ]
    }
    return jsonify(test_data)

@app.route('/api/test_compare')
def api_test_compare():
    test_data = {
        "Test for Bug": [
          {"qnumber": 1, "description": 0, "time_taken": 20},
          {"qnumber": 2, "description": None, "time_taken": 25},
          {"qnumber": 3, "description": "", "time_taken": 18}
        ],
        "Alice": [
          {"qnumber": 1, "description": "Photosynthesis uses sunlight to make food.", "time_taken": 20},
          {"qnumber": 2, "description": "Compiled languages run faster than interpreted.", "time_taken": 25},
          {"qnumber": 3, "description": "The Industrial Revolution began in Britain.", "time_taken": 18}
        ],
        "Bob": [
          {"qnumber": 1, "description": "Photosynthesis uses sunlight to create food.", "time_taken": 21},
          {"qnumber": 2, "description": "Compiled languages run quicker than interpreted.", "time_taken": 26},
          {"qnumber": 3, "description": "The Industrial Revolution started in Britain.", "time_taken": 19}
        ],
        "Charlie": [
          {"qnumber": 1, "description": "Photosynthesis uses sunlite to make food.", "time_taken": 22},
          {"qnumber": 2, "description": "Compiled languages run faster than interprted.", "time_taken": 24},
          {"qnumber": 3, "description": "The Industrial Revoluton began in Britain.", "time_taken": 20}
        ],
        "Dana": [
          {"qnumber": 1, "description": "Photosynthesis uses sunlight to create food.", "time_taken": 23},
          {"qnumber": 2, "description": "Compiled languages run faster than interprted.", "time_taken": 27},
          {"qnumber": 3, "description": "The French Revolution began in France.", "time_taken": 21}
        ],
        "Eve": [
          {"qnumber": 1, "description": "Photosynthesis uses sunlight to make foud.", "time_taken": 19},
          {"qnumber": 2, "description": "Compiled languages run faster than interpreted.", "time_taken": 23},
          {"qnumber": 3, "description": "The Industrial Revolution began in Britan.", "time_taken": 17}
        ],
        "Frank": [
          {"qnumber": 1, "description": "Respiration releases energy from glucose.", "time_taken": 24},
          {"qnumber": 2, "description": "Scripting languages are often interpreted.", "time_taken": 28},
          {"qnumber": 3, "description": "The Civil War occurred in America.", "time_taken": 22}
        ],
        "Amir": [
        {"qnumber": 1, "description": "Artificial intelligence is the simulation of human intelligence in machines.", "time_taken": 40},
        {"qnumber": 2, "description": "Machine learning is a subset of AI that involves training algorithms on data.", "time_taken": 50},
        {"qnumber": 3, "description": "Python is widely used for AI development due to its simplicity and libraries.", "time_taken": 30}
      ],
      "Kimia": [
        {"qnumber": 1, "description": "Artificial intelligence is the simulation of human intelligence in machines.", "time_taken": 42},
        {"qnumber": 2, "description": "Machine learning is a subset of AI that involves training algorithms on data.", "time_taken": 52},
        {"qnumber": 3, "description": "Python is widely used for AI development due to its simplicity and libraries.", "time_taken": 32}
      ],
      "Negar": [
        {"qnumber": 1, "description": "Quantum computing uses quantum bits to perform computations.", "time_taken": 35},
        {"qnumber": 2, "description": "Blockchain is a decentralized ledger technology.", "time_taken": 45},
        {"qnumber": 3, "description": "JavaScript is essential for web development.", "time_taken": 25}
      ],
      "Farshad": [
        {"qnumber": 1, "description": "Quantum computing uses quantum bits to perform computations.", "time_taken": 37},
        {"qnumber": 2, "description": "Blockchain is a decentralized ledger technology.", "time_taken": 47},
        {"qnumber": 3, "description": "JavaScript is essential for web development.", "time_taken": 27}
      ],
      "Arad": [
        {"qnumber": 1, "description": "Renewable energy sources include solar and wind power.", "time_taken": 38},
        {"qnumber": 2, "description": "Climate change is a pressing global issue.", "time_taken": 48},
        {"qnumber": 3, "description": "C++ is used for high-performance applications.", "time_taken": 28}
      ],
      "Bita": [
        {"qnumber": 1, "description": "Renewable energy sources include solar and wind power.", "time_taken": 40},
        {"qnumber": 2, "description": "The internet is a global network of computers.", "time_taken": 50},
        {"qnumber": 3, "description": "HTML is used for creating web pages.", "time_taken": 30}
      ]
    }
    users = list(test_data.keys())
    results = []
    for i in range(len(users)):
        for j in range(i+1, len(users)):
            user1, user2 = users[i], users[j]
            qlist1, qlist2 = test_data[user1], test_data[user2]
            for q in range(1, 4):
                ans1 = next((item for item in qlist1 if item['qnumber'] == q), None)
                ans2 = next((item for item in qlist2 if item['qnumber'] == q), None)
                if ans1 and ans2:
                    desc1 = str(ans1['description']) if ans1['description'] else ''
                    desc2 = str(ans2['description']) if ans2['description'] else ''
                    if desc1.strip() and desc2.strip():
                        vectorizer = TfidfVectorizer().fit([desc1, desc2])
                        vecs = vectorizer.transform([desc1, desc2])
                        sim = cosine_similarity(vecs[0:1], vecs[1:2])[0][0]
                        lcs = find_lcs(desc1, desc2)
                    else:
                        sim = None
                        lcs = ''
                    t1 = ans1['time_taken'] if ans1['time_taken'] is not None else None
                    t2 = ans2['time_taken'] if ans2['time_taken'] is not None else None
                    time_diff = abs(t1 - t2) if t1 is not None and t2 is not None else None
                    results.append({
                        'user1': user1,
                        'user2': user2,
                        'qnumber': q,
                        'desc1': desc1,
                        'desc2': desc2,
                        'similarity': round(sim, 3) if sim is not None else '',
                        'lcs': lcs,
                        'time1': t1,
                        'time2': t2,
                        'time_diff': time_diff
                    })
    return jsonify(results)

if __name__ == '__main__':
    app.run(debug=True)
