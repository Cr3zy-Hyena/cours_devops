from flask import Flask, request, jsonify, render_template
from calc import calculate

app = Flask(__name__, template_folder='templates')


@app.route('/', methods=['GET'])
def index():
  return render_template('index.html')


@app.route('/calculer', methods=['POST'])
def calculer():
  data = request.get_json(silent=True)
  if not data:
    return jsonify({'error': 'JSON attendu'}), 400

  a = data.get('a')
  b = data.get('b')
  op = data.get('op', 'add')

  result = calculate(a, b, op)
  if isinstance(result, dict) and 'error' in result:
    return jsonify(result), 400

  return jsonify({'result': result})


if __name__ == '__main__':
  app.run(debug=True, host='0.0.0.0', port=5000)
