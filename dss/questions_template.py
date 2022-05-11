from flask import Flask, render_template


app = Flask(__name__)
app.url_map.strict_slashes = False


@app.route("/") 
def home():
    return render_template('questions_template.html')

if __name__ == '__main__': 
    app.run(debug=True) 
