# بخش 4: تحلیل پاسخ کاربران
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

    current_total_time = sum(current_user.get('timing', {}).values()) if current_user.get('timing') else 0
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
