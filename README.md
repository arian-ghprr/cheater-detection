# cheater-detection
Capabilities:
1.User Data Collection & Storage

Users access a quiz page and submit their answers.

User information (name, answers, login time, submission time) is collected.

Data is saved into a local JSON file named users_data.json.

2. Text Similarity Analysis
   
The app analyzes how similar users' answers are using NLP techniques:

Cosine Similarity measures semantic closeness between two answers.

Longest Common Subsequence (LCS) identifies the longest shared sequence of characters.

For each question, the app finds and reports the user with the most similar answer to the current one.

3. Time Pattern Analysis
   
The app records how long users take to answer each question.

Using Pearson Correlation, it checks how similar the timing patterns are between users.

If a user's timing is very closely correlated (>0.95) with another, it flags it as a potential suspicious pattern (e.g., copying or collaboration).

4. Web Pages Rendering
   
The app serves several HTML pages:

welcome.html: Welcome/landing page

quiz.html: Quiz form for submitting answers

results.html: Page to show analysis results

test_panel.html: Possibly for testing or admin use
5. REST API Endpoints

The app provides several API routes:

/api/analyze: Main analysis logic (text + time)

/api/save_user: Save user data to file

/api/clear_users: Reset all user data

/api/test_data and /api/test_compare: Simulated data for automated testing & comparison

 6. Ideal for Use Cases Like:

Cheating detection in quizzes or collaborative exams

Text analysis in surveys or open-form responses

Educational tools to analyze thinking patterns

Intro-level NLP/AI experiments


![Diagram](https://github.com/user-attachments/assets/16b0f320-fb9a-495f-bfdf-9eeff74bcd52)
