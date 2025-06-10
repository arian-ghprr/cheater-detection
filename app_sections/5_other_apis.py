# بخش 5: سایر APIها
@app.route('/api/save_user', methods=['POST'])
def api_save_user():
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'message': 'داده‌ای ارسال نشده است.'}), 400
    try:
        login_time = data.get('login_time')
        submit_time = data.get('submit_time')
        if login_time and submit_time:
            t1 = pd.to_datetime(login_time)
            t2 = pd.to_datetime(submit_time)
            duration = t2 - t1
            duration_str = str(duration).split('.')[0]
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
