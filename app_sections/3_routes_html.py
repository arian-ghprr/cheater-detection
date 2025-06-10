# بخش 3: نمایش صفحات HTML
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
