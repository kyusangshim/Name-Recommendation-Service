#!/usr/bin/env python
# coding: utf-8

# In[2]:


from flask import Flask, request, render_template
import os
import openai
import re
import pymysql

app = Flask(__name__, template_folder='chatgpt_html_dir')

os.environ['OPENAI_API_KEY'] = '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'
openai.api_key = os.getenv("OPENAI_API_KEY")

host = "namedb.c0yqsa6ec0oa.ap-northeast-2.rds.amazonaws.com"
port = 3306
user = "root"
password = "iceproject"
database = "namedb"

# 데이터베이스 insert 함수
def insert_data(keyword, target, goal, source, mood, style, name_meaning):
    conn = pymysql.connect(host=host, port=port, user=user, password=password, database = database)
    cursor = conn.cursor()

    for i in range(len(name_meaning)):
        cursor.execute('''
            INSERT INTO name (keyword, target_age, purpose, source, atmosphere, style, name_meaning)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        ''', (keyword, target, goal, source, mood, style, name_meaning[i]))

    conn.commit()
    conn.close()
    
@app.route('/')
def student():
    return render_template("my_html_page.html")


@app.route('/result', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        keyword = f"키워드: {request.form['keyword']}"
        target = f"주 타겟층: {request.form['target']}"
        goal = f"용도: {request.form['goal']}"
        source_list = [request.form.get('culture',''),request.form.get('celebrity',''),request.form.get('location',''),request.form.get('food',''),request.form.get('biological',''),request.form.get('item',''),request.form.get('other',''),request.form.get('none','')]
        result = ""
        for i in range(len(source_list)):
            if source_list[i] == '':
                continue
            else:
                result += source_list[i] + "&"
                
        result = result.rstrip('&')
        source = "소스: " + result + " 가(이) 어우러진 이름"
        style_list = [request.form.get('style1',''),request.form.get('style2','')]
        result2 = "" 
        for i in range(len(style_list)):
            if style_list[i] == '':
                continue
            else:
                result2 += style_list[i] + "&"
                
        result2 = result2.rstrip('&')
        style = "단어 조건: " + result2 + " 가(이) 조건을 만족하는 이름"
        mood = f"분위기: {request.form['mood']}"
        
        result1 = f"{keyword}\n{target}\n{goal}\n{source}\n{mood}\n{style}"
        result2 = f"<조건>\n{result1}\n\n위 조건에 부합하는 새로운 영어 이름 5개와 한국어로 의미도 자세하게 같이 출력해줘."
        
        messages = []
        user_content = result2
        messages.append({"role": "user", "content" : f"{user_content}"})
        
        completion = openai.ChatCompletion.create(model="ft:gpt-3.5-turbo-0613:personal::8Kit0xFq", messages=messages)

     
        result = completion.choices[0].message["content"]

        final_result = re.sub(r'\d+\.', '', result)
        
        #데이터베이스 적재
        name_meaning = re.findall(r'\d+\. (.*?)(?=\n\d+\.|\Z)', result, re.DOTALL)
        
        insert_data(request.form['keyword'], request.form['target'], request.form['goal'], source, request.form['mood'], style, name_meaning)

        
        # 결과를 개행 문자("\n")를 기준으로 분할하여 리스트로 변환
        results = final_result.split("\n")
        

        # 결과에서 불필요한 공백 및 빈 문자열 제거
        results = [result.strip() for result in results if result.strip()]
        
        
        results_dict = {}
        
        results_dict["names"] = [name_and_meaning.split("-")[0] if " - " in name_and_meaning else name_and_meaning.split(":")[0] for name_and_meaning in results]
        results_dict["descriptions"] = [name_and_meaning.split("-")[1] if " - " in name_and_meaning else name_and_meaning.split(":")[1] for name_and_meaning in results]

        # 결과를 HTML 템플릿에 전달
        return render_template('my_html_page_result.html', results=results_dict)
    
    return render_template('my_html_page_result.html', result=None)

if __name__ == '__main__':
    app.run(debug=True)

