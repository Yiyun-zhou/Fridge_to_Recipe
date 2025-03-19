from flask import Flask, request, jsonify, render_template #flask创建web应用
import sqlite3 #sqlite数据库
import openai
import os
from dotenv import load_dotenv

app = Flask(__name__)

# 初始化数据库
def init_db():
    conn = sqlite3.connect('fridge.db')
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS ingredients (id INTEGER PRIMARY KEY, name TEXT)')
    conn.commit()
    conn.close()

# 初始化 OpenAI
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("Error: OPENAI_API_KEY not found!")

print("Loaded API Key:", api_key[:5] + "********")  # 只打印前5位，避免泄露

# 初始化 OpenAI 客户端
client = openai.OpenAI(api_key=api_key)


# 添加食材
@app.route('/ingredients', methods=['POST'])
def add_ingredient():
    data = request.json
    name = data.get('name')
    conn = sqlite3.connect('fridge.db')
    c = conn.cursor()
    c.execute('INSERT INTO ingredients (name) VALUES (?)', (name,))
    conn.commit()
    conn.close()
    return jsonify({'id': c.lastrowid})

# 获取食材列表
@app.route('/ingredients', methods=['GET'])
def get_ingredients():
    conn = sqlite3.connect('fridge.db')
    c = conn.cursor()
    c.execute('SELECT * FROM ingredients')
    ingredients = c.fetchall()
    conn.close()
    return jsonify(ingredients)

# 生成菜谱
@app.route('/generate-recipe', methods=['POST'])
def generate_recipe():
    data = request.json
    print('收到请求数据', data)
    health_goal = data.get('healthGoal', '无')
    taste_preference = data.get('tastePreference', '无')
    meal = data.get('meal', '无')  # 获取用户选择的餐别
    allergy = data.get('allergy', '无')
    servings = data.get('servings', 1)
    extrainfo = data.get('additionalRequirements', '').strip()
    mys_code = data.get('lovecode', '').strip()

    conn = sqlite3.connect('fridge.db')
    c = conn.cursor()
    c.execute('SELECT name FROM ingredients')
    ingredients = [row[0] for row in c.fetchall()]
    conn.close()

    prompt = f"你是一个顶尖营养师和厨师，请根据以下食材生成一个菜谱（注意：只要食材和做法，不需要用到所有食材）：{', '.join(ingredients)}。"
    if health_goal != '无':
        if health_goal == '减脂':
            prompt += f"健康目标：{health_goal}。请在菜谱最后给出对减脂目标较为有用的营养值，例如卡路里。"
        elif health_goal == '增肌':
            prompt += f"健康目标：{health_goal}。请在菜谱最后给出对增肌目标较为有用的营养值。"
        else:
            prompt += f"健康目标：{health_goal}。"
    if taste_preference != '无':
        prompt += f"口味偏好：{taste_preference}。"
    if meal != '无':
        prompt += f"餐别：{meal}。"
    if allergy != '无':
        prompt += f"过敏：{allergy}。"
    prompt += f"用餐人数：{servings}人。"

    if extrainfo:
        prompt += f'额外要求：{extrainfo}。'

    if mys_code == '0328':
        prompt += '请在output第一行写,[欢迎尊贵vip: 来自美国的孙女士和豆包博士🐻],并且菜谱除了给人的,加上一份给12岁的poodle豆包的菜谱,output直接称呼poodle为豆包就可以'
    if mys_code == '0310':
        prompt += '请在output第一行写,[欢迎尊贵vip: 来自中国的吴老阿太和虎太郎🐯],并且菜谱除了给人的,加上一份给小猫虎太郎的菜谱,output直接称呼小猫为虎太郎就可以'
    if mys_code == '1112':
        prompt += '请在output第一行写,[欢迎尊贵vip: 来自英国的沈姐和小比格]'
    if mys_code == '1125':
        prompt += '请在output第一行写,[欢迎尊贵vip: 来自外太空的小周和她的帅哥们]'
    
    print("开始生成菜谱")
    try:
        response = client.chat.completions.create(
            model='gpt-3.5-turbo',
            messages=[{'role': 'user', 'content': prompt}]
        )
        print("菜谱生成完毕")
        recipe = response.choices[0].message.content
        print("返回的菜谱：", recipe)
        return jsonify({'recipe': recipe})
    except Exception as e:
        print(f"生成菜谱时出错: {e}")
        return jsonify({'error': '生成菜谱时出错'})


# 删除食材
@app.route('/ingredients/<int:id>', methods=['DELETE'])
def delete_ingredient(id):
    conn = sqlite3.connect('fridge.db')
    c = conn.cursor()
    c.execute('DELETE FROM ingredients WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

# 首页
@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
